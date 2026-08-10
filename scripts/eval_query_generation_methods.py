#!/usr/bin/env python3
"""Generate and score versioned single-query methods in the query design.

The generator sees only the current user question and the approved projection of
the saved BusinessSnapshot. Retrieval is executed through the public CLI so this
eval cannot silently diverge from the product search path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.snapshot import BusinessSnapshot  # noqa: E402


DEFAULT_CASES = ROOT / "evals" / "advisor_search_query_cases_enriched_labels.jsonl"
DEFAULT_GUIDE = ROOT / "evals" / "query_generation" / "corpus_guide_v1.json"
DEFAULT_RUNS_DIR = ROOT / "evals" / "runs" / "query_generation" / "v1"
DEFAULT_REPORT = ROOT / "evals" / "reports" / "query_generation_methods_dev.md"
DEFAULT_SUMMARY = ROOT / "evals" / "reports" / "query_generation_methods_dev_summary.json"
DEFAULT_CASE_RESULTS = ROOT / "evals" / "reports" / "query_generation_methods_dev_cases.jsonl"

METHODS = (
    "raw_question",
    "model_rewrite",
    "guided_model_rewrite",
    "guided_model_rewrite_v2",
)
DEFAULT_METHODS = METHODS[:3]
MODEL_METHODS = METHODS[1:]
GUIDED_METHODS = ("guided_model_rewrite", "guided_model_rewrite_v2")
METHOD_VERSIONS = {
    "raw_question": "single-query-methods.v1",
    "model_rewrite": "single-query-methods.v1",
    "guided_model_rewrite": "single-query-methods.v1",
    "guided_model_rewrite_v2": "single-query-methods.v2",
}
PROMPT_VERSIONS = {
    "model_rewrite": "query-generation-prompt.v1",
    "guided_model_rewrite": "query-generation-prompt.v1",
    "guided_model_rewrite_v2": "query-generation-prompt.v2",
}
SMOKE_CASE_IDS = (
    "searchq_v1_001",
    "searchq_v1_010",
    "searchq_v1_015",
    "searchq_v1_021",
    "searchq_v1_030",
)
TOKEN_RE = re.compile(r"tokens used\s+([0-9,]+)", re.IGNORECASE)

BASE_INSTRUCTION = """You generate one query for searching a source corpus.

The system has already decided that source search is appropriate. Write the single
query most likely to retrieve passages that directly answer the user's current
question.

Use saved business facts only when they change what evidence is needed. Do not stuff
the query with background details merely because they are available. Do not answer the
question. Do not provide a rationale, subject label, namespace, filter, or multiple
queries. Do not invent facts. Do not use tools.

Return only the JSON object required by the response schema."""

GUIDED_EXTENSION = """Use the corpus guide below when it is relevant. It describes the
source's vocabulary and the relationships between its concepts. Translate ordinary
user language into source terminology when that will help retrieval, but do not copy
irrelevant guide terms into the query."""

GUIDED_EXTENSION_V2 = """Use the corpus guide as a translation reference, not as a
checklist. Translate the user's language into the source's canonical terminology when
that will help retrieve a passage that directly answers the question.

Preserve the user's full information need. Include every concept needed to express the
mechanism, relationship, comparison, sequence, or combined system the user asks about;
there is no fixed number of concepts. Include relevant business context only when it
changes or disambiguates the evidence needed. Do not introduce a concept merely because
the guide lists it as related or nearby. Do not speculate about the answer or add a
mechanism the user did not ask about. Make the query only as long as necessary without
dropping essential meaning."""

OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "minLength": 1,
            "maxLength": 400,
            "pattern": r"^[^\r\n]+$",
        }
    },
    "required": ["query"],
    "additionalProperties": False,
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _prune_empty(value: Any) -> Any:
    if isinstance(value, dict):
        pruned = {key: _prune_empty(item) for key, item in value.items()}
        return {key: item for key, item in pruned.items() if item not in (None, "", [], {})}
    if isinstance(value, list):
        pruned = [_prune_empty(item) for item in value]
        return [item for item in pruned if item not in (None, "", [], {})]
    return value


def generator_visible_snapshot(snapshot_path: Path) -> dict[str, Any]:
    snapshot = BusinessSnapshot.load(snapshot_path).to_dict()
    visible = {
        key: snapshot[key]
        for key in ("business", "money_model", "economics", "problem")
    }
    return _prune_empty(visible)


def generator_visible_guide(guide_path: Path) -> dict[str, Any]:
    payload = json.loads(guide_path.read_text(encoding="utf-8"))
    visible_fields = payload["generator_visible_fields"]
    entries = [
        {field: entry[field] for field in visible_fields}
        for entry in payload["entries"]
    ]
    return {"version": payload["version"], "entries": entries}


def build_prompt(
    case: dict[str, Any],
    method: str,
    *,
    guide_path: Path = DEFAULT_GUIDE,
) -> str:
    if method not in MODEL_METHODS:
        raise ValueError(f"prompt is only defined for model methods, got {method!r}")
    snapshot_path = ROOT / case["snapshot_fixture_path"]
    blocks = [
        BASE_INSTRUCTION,
        "## Current user question\n\n" + case["user_turn"],
        "## Saved business facts\n\n```json\n"
        + json.dumps(generator_visible_snapshot(snapshot_path), indent=2, sort_keys=True)
        + "\n```",
    ]
    if method in GUIDED_METHODS:
        guided_extension = (
            GUIDED_EXTENSION_V2
            if method == "guided_model_rewrite_v2"
            else GUIDED_EXTENSION
        )
        blocks.extend(
            [
                guided_extension,
                "## Corpus guide\n\n```json\n"
                + json.dumps(generator_visible_guide(guide_path), indent=2, sort_keys=True)
                + "\n```",
            ]
        )
    return "\n\n".join(blocks).rstrip() + "\n"


def validate_query(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("query must be a string")
    query = value.strip()
    if not query:
        raise ValueError("query must not be empty")
    if "\n" in query or "\r" in query:
        raise ValueError("query must be one line")
    if len(query) > 400:
        raise ValueError("query must be no more than 400 characters")
    return query


def raw_query(case: dict[str, Any]) -> str:
    return validate_query(" ".join(case["user_turn"].split()))


def run_dir_for(runs_dir: Path, model: str, method: str, case_id: str) -> Path:
    return runs_dir / model / method / case_id


def codex_command(model: str, workspace: Path, schema_path: Path, output_path: Path) -> list[str]:
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        model,
        "--cd",
        str(workspace),
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "-",
    ]


def _tokens_used(stdout: str, stderr: str) -> int | None:
    match = TOKEN_RE.search(stdout + "\n" + stderr)
    return int(match.group(1).replace(",", "")) if match else None


def generate_case(
    case: dict[str, Any],
    method: str,
    *,
    model: str,
    guide_path: Path,
    runs_dir: Path,
    timeout: int,
    force: bool,
) -> Path:
    case_dir = run_dir_for(runs_dir, model, method, case["case_id"])
    generation_path = case_dir / "generation.json"
    if generation_path.exists() and not force:
        return generation_path
    case_dir.mkdir(parents=True, exist_ok=True)

    if method == "raw_question":
        write_json(
            generation_path,
            {
                "case_id": case["case_id"],
                "created_at": utc_now(),
                "guide_version": None,
                "harness": "literal_pass_through",
                "latency_ms": 0.0,
                "method": method,
                "method_version": METHOD_VERSIONS[method],
                "model": None,
                "prompt_version": None,
                "query": raw_query(case),
                "tokens_used_reported_by_codex": None,
                "valid": True,
            },
        )
        return generation_path

    prompt = build_prompt(case, method, guide_path=guide_path)
    (case_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mma-query-generation-") as temp_name:
        workspace = Path(temp_name)
        schema_path = workspace / "query.schema.json"
        output_path = workspace / "final.json"
        schema_path.write_text(json.dumps(OUTPUT_SCHEMA, indent=2) + "\n", encoding="utf-8")
        try:
            completed = subprocess.run(
                codex_command(model, workspace, schema_path, output_path),
                input=prompt,
                text=True,
                cwd=ROOT,
                capture_output=True,
                timeout=timeout,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            returncode = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            returncode = 124
            timed_out = True
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        (case_dir / "codex_stdout.txt").write_text(stdout, encoding="utf-8")
        (case_dir / "codex_stderr.txt").write_text(stderr, encoding="utf-8")

        payload: dict[str, Any] = {
            "case_id": case["case_id"],
            "created_at": utc_now(),
            "guide_version": generator_visible_guide(guide_path)["version"]
            if method in GUIDED_METHODS
            else None,
            "harness": "codex_cli_bounded_generation",
            "latency_ms": latency_ms,
            "method": method,
            "method_version": METHOD_VERSIONS[method],
            "model": model,
            "prompt_version": PROMPT_VERSIONS[method],
            "returncode": returncode,
            "tokens_used_reported_by_codex": _tokens_used(stdout, stderr),
            "valid": False,
        }
        if timed_out:
            payload["error"] = "codex_exec_timeout"
        elif returncode != 0:
            payload["error"] = "codex_exec_failed"
        elif not output_path.exists():
            payload["error"] = "missing_final_output"
        else:
            raw_final = output_path.read_text(encoding="utf-8")
            (case_dir / "codex_final.json").write_text(raw_final, encoding="utf-8")
            try:
                final = json.loads(raw_final)
                payload["query"] = validate_query(final.get("query"))
                payload["valid"] = True
            except (json.JSONDecodeError, ValueError, AttributeError) as exc:
                payload["error"] = f"invalid_final_output: {exc}"
        write_json(generation_path, payload)
    return generation_path


def select_cases(
    cases: list[dict[str, Any]],
    *,
    case_ids: list[str] | None,
    limit: int | None,
    smoke: bool,
) -> list[dict[str, Any]]:
    selected_ids = set(SMOKE_CASE_IDS if smoke else (case_ids or []))
    selected = [case for case in cases if not selected_ids or case["case_id"] in selected_ids]
    if selected_ids:
        found = {case["case_id"] for case in selected}
        missing = sorted(selected_ids - found)
        if missing:
            raise ValueError(f"unknown case IDs: {', '.join(missing)}")
    return selected[:limit] if limit is not None else selected


def run_cli_search(
    query: str,
    backend: str,
    *,
    vector_store: str,
    top_k: int,
    timeout: int,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [
        sys.executable,
        "-m",
        "money_model_architect.cli",
        "search",
        query,
        "--backend",
        backend,
        "--top-k",
        str(top_k),
    ]
    if backend in {"vector", "hybrid"}:
        command.extend(["--vector-store", vector_store])
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
    except subprocess.TimeoutExpired as exc:
        return None, {
            "command": command,
            "error": "cli_timeout",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "stderr": exc.stderr or "",
        }
    meta = {
        "command": command,
        "latency_ms": latency_ms,
        "returncode": completed.returncode,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        meta["error"] = "cli_failed"
        return None, meta
    try:
        return json.loads(completed.stdout), meta
    except json.JSONDecodeError as exc:
        meta["error"] = f"invalid_cli_json: {exc}"
        return None, meta


def first_useful_rank(returned_ids: list[str], useful_ids: set[str]) -> int | None:
    for rank, chunk_id in enumerate(returned_ids, start=1):
        if chunk_id in useful_ids:
            return rank
    return None


def score_result_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    valid_rows = [row for row in rows if row.get("error") is None]
    completed = len(valid_rows)
    ranks = [row["first_useful_rank"] for row in valid_rows if row["first_useful_rank"] is not None]
    latencies = [row["retrieval_latency_ms"] for row in valid_rows]
    return {
        "cases": total,
        "completed_cases": completed,
        "coverage_pct": round(100 * completed / total, 1) if total else None,
        "execution_errors": total - completed,
        "hit_at_1": sum(row["first_useful_rank"] == 1 for row in valid_rows),
        "hit_at_1_pct": round(100 * sum(row["first_useful_rank"] == 1 for row in valid_rows) / completed, 1)
        if completed
        else None,
        "hit_at_3": sum(row["first_useful_rank"] is not None and row["first_useful_rank"] <= 3 for row in valid_rows),
        "hit_at_3_pct": round(
            100
            * sum(row["first_useful_rank"] is not None and row["first_useful_rank"] <= 3 for row in valid_rows)
            / completed,
            1,
        )
        if completed
        else None,
        "hit_at_5": len(ranks),
        "hit_at_5_pct": round(100 * len(ranks) / completed, 1) if completed else None,
        "mean_first_useful_rank": round(sum(ranks) / len(ranks), 3) if ranks else None,
        "mean_retrieval_latency_ms": round(statistics.mean(latencies), 1) if latencies else None,
        "misses": [row["case_id"] for row in valid_rows if row["first_useful_rank"] is None],
        "missing_cases": [row["case_id"] for row in rows if row.get("error") is not None],
    }


def summarize_generation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(row["latency_ms"]) for row in rows]
    reported_tokens = [
        int(row["tokens_used_reported_by_codex"])
        for row in rows
        if row.get("tokens_used_reported_by_codex") is not None
    ]
    return {
        "cases": len(rows),
        "valid_cases": sum(bool(row.get("valid")) for row in rows),
        "mean_latency_ms": round(statistics.mean(latencies), 1) if latencies else None,
        "p50_latency_ms": round(statistics.median(latencies), 1) if latencies else None,
        "total_codex_reported_tokens": sum(reported_tokens) if reported_tokens else None,
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Query Generation Method Comparison",
        "",
        f"**Created:** {summary['created_at']}",
        f"**Dataset:** `{summary['cases_file']}` ({summary['case_count']} exposed development cases)",
        f"**Generation model:** `{summary['model']}` for model-driven conditions",
        f"**Method version:** `{summary['method_version']}`",
        "",
        "This is development evidence, not the untouched holdout decision. Every query was retrieved through the public CLI with no subject filter.",
        "",
        "## Generation",
        "",
        "The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.",
        "",
        "| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in summary["methods"]:
        result = summary["generation"][method]
        lines.append(
            f"| `{method}` | {result['valid_cases']}/{result['cases']} | "
            f"{result['mean_latency_ms'] or 0} ms | {result['p50_latency_ms'] or 0} ms | "
            f"{result['total_codex_reported_tokens'] or 0} |"
        )
    lines.extend(
        [
            "",
            "## Retrieval",
            "",
            "Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.",
            "Rows with incomplete coverage are descriptive only and must not be compared directly with complete 30-case rows.",
            "",
            "| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Mean retrieval latency | Errors |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for method in summary["methods"]:
        for backend in summary["backends"]:
            result = summary["results"][method][backend]
            rank = result["mean_first_useful_rank"]
            lines.append(
                f"| `{method}` | `{backend}` | {result['completed_cases']}/{result['cases']} | "
                f"{result['hit_at_1_pct']:.1f}% | {result['hit_at_3_pct']:.1f}% | {result['hit_at_5_pct']:.1f}% | "
                f"{rank if rank is not None else '-'} | {result['mean_retrieval_latency_ms'] or '-'} ms | "
                f"{result['execution_errors']} |"
            )
    lines.extend(["", "## Misses", ""])
    for method in summary["methods"]:
        for backend in summary["backends"]:
            misses = summary["results"][method][backend]["misses"]
            lines.append(f"- `{method}` / `{backend}`: {', '.join(misses) if misses else 'none'}")
    incomplete = [
        (method, backend, summary["results"][method][backend]["missing_cases"])
        for method in summary["methods"]
        for backend in summary["backends"]
        if summary["results"][method][backend]["missing_cases"]
    ]
    if incomplete:
        lines.extend(["", "## Incomplete executions", ""])
        for method, backend, missing in incomplete:
            lines.append(f"- `{method}` / `{backend}` missing: {', '.join(missing)}")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Prompts and the corpus guide may be revised using these exposed development cases, with every revision versioned. No method should be promoted until the frozen finalists are evaluated on the independently reviewed holdout.",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_generate(args: argparse.Namespace) -> int:
    cases = select_cases(
        load_jsonl(args.cases),
        case_ids=args.case_ids,
        limit=args.limit,
        smoke=args.smoke,
    )
    for method in args.methods:
        for case in cases:
            print(f"generating {method} {case['case_id']}", file=sys.stderr)
            generate_case(
                case,
                method,
                model=args.model,
                guide_path=args.guide,
                runs_dir=args.runs_dir,
                timeout=args.timeout,
                force=args.force,
            )
    rows = []
    for case in cases:
        for method in args.methods:
            path = run_dir_for(args.runs_dir, args.model, method, case["case_id"]) / "generation.json"
            rows.append(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps({"cases": len(cases), "methods": args.methods, "generations": rows}, indent=2))
    return 0 if all(row.get("valid") for row in rows) else 1


def cmd_score(args: argparse.Namespace) -> int:
    cases = select_cases(
        load_jsonl(args.cases),
        case_ids=args.case_ids,
        limit=args.limit,
        smoke=False,
    )
    rows: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {
        method: {backend: [] for backend in args.backends} for method in args.methods
    }
    for method in args.methods:
        for case in cases:
            case_dir = run_dir_for(args.runs_dir, args.model, method, case["case_id"])
            generation_path = case_dir / "generation.json"
            if not generation_path.exists():
                raise SystemExit(f"missing generation artifact: {generation_path}")
            generation = json.loads(generation_path.read_text(encoding="utf-8"))
            if not generation.get("valid"):
                raise SystemExit(f"invalid generation artifact: {generation_path}")
            query = generation["query"]
            for backend in args.backends:
                retrieval_dir = case_dir / "retrieval"
                retrieval_path = retrieval_dir / f"{backend}.json"
                meta_path = retrieval_dir / f"{backend}_meta.json"
                if retrieval_path.exists() and meta_path.exists() and not args.force:
                    response = json.loads(retrieval_path.read_text(encoding="utf-8"))
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                elif args.existing_only:
                    response = None
                    meta = {
                        "error": "missing_retrieval_artifact",
                        "latency_ms": 0.0,
                    }
                else:
                    print(f"retrieving {method} {backend} {case['case_id']}", file=sys.stderr)
                    response, meta = run_cli_search(
                        query,
                        backend,
                        vector_store=args.vector_store,
                        top_k=args.top_k,
                        timeout=args.timeout,
                    )
                    write_json(meta_path, meta)
                    if response is not None:
                        write_json(retrieval_path, response)
                returned_ids = [item["id"] for item in response.get("source_material", [])] if response else []
                useful_ids = set(case["known_useful_chunk_ids"])
                rank = first_useful_rank(returned_ids, useful_ids)
                row = {
                    "backend": backend,
                    "case_id": case["case_id"],
                    "error": meta.get("error"),
                    "first_useful_rank": rank,
                    "method": method,
                    "query": query,
                    "retrieval_latency_ms": meta["latency_ms"],
                    "returned_chunk_ids": returned_ids,
                    "useful_returned_chunk_ids": [chunk_id for chunk_id in returned_ids if chunk_id in useful_ids],
                }
                rows.append(row)
                grouped[method][backend].append(row)

    generation_rows = {
        method: [
            json.loads(
                (
                    run_dir_for(args.runs_dir, args.model, method, case["case_id"])
                    / "generation.json"
                ).read_text(encoding="utf-8")
            )
            for case in cases
        ]
        for method in args.methods
    }
    summary = {
        "backends": args.backends,
        "case_count": len(cases),
        "cases_file": rel_path(args.cases),
        "created_at": utc_now(),
        "method_version": ", ".join(
            sorted({METHOD_VERSIONS[method] for method in args.methods})
        ),
        "method_versions": {
            method: METHOD_VERSIONS[method] for method in args.methods
        },
        "prompt_versions": {
            method: PROMPT_VERSIONS.get(method) for method in args.methods
        },
        "methods": args.methods,
        "model": args.model,
        "generation": {
            method: summarize_generation(generation_rows[method])
            for method in args.methods
        },
        "results": {
            method: {
                backend: score_result_rows(grouped[method][backend])
                for backend in args.backends
            }
            for method in args.methods
        },
        "top_k": args.top_k,
        "vector_store": args.vector_store,
    }
    write_json(args.summary, summary)
    write_jsonl(args.case_results, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps({"report": rel_path(args.report), "summary": rel_path(args.summary)}, indent=2))
    return 0


def add_case_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--case-ids", nargs="+")
    parser.add_argument("--limit", type=int)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Generate and preserve one query per case and method.")
    add_case_filters(generate)
    generate.add_argument("--guide", type=Path, default=DEFAULT_GUIDE)
    generate.add_argument("--methods", nargs="+", choices=METHODS, default=list(DEFAULT_METHODS))
    generate.add_argument("--model", default="gpt-5.5")
    generate.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    generate.add_argument("--timeout", type=int, default=300)
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--smoke", action="store_true", help="Use the five predeclared unscored readiness cases.")
    generate.set_defaults(func=cmd_generate)

    score = sub.add_parser("score", help="Run generated queries through the real CLI and score chunk IDs.")
    add_case_filters(score)
    score.add_argument("--methods", nargs="+", choices=METHODS, default=list(DEFAULT_METHODS))
    score.add_argument("--backends", nargs="+", choices=("bm25", "vector", "hybrid"), default=["bm25", "hybrid"])
    score.add_argument("--model", default="gpt-5.5")
    score.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    score.add_argument("--vector-store", choices=("local", "pinecone"), default="local")
    score.add_argument("--top-k", type=int, default=5)
    score.add_argument("--timeout", type=int, default=300)
    score.add_argument("--force", action="store_true")
    score.add_argument(
        "--existing-only",
        action="store_true",
        help="Summarize only retrieval artifacts already on disk; record missing cases without executing them.",
    )
    score.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    score.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    score.add_argument("--case-results", type=Path, default=DEFAULT_CASE_RESULTS)
    score.set_defaults(func=cmd_score)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
