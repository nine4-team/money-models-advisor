#!/usr/bin/env python3
"""Evaluate the advisor's search gate through isolated Codex agent trials.

This runner deliberately stops before retrieval and answer generation. The
deterministic harness loads current business context through the real CLI; each
model then makes only the semantic search/no-search choice. The acting runtime
contains no golden cases, reports, prior trials, or evaluator labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "advisor_search_decision_cases.jsonl"
DEFAULT_MODELS = ("gpt-5.5", "gpt-5.4-mini")
RUNTIME_FILES = ("AGENTS.md", "pyproject.toml")
RUNTIME_TREES = ("src",)
DECISIONS = ("search_source_material", "no_search")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [case.get("case_id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("case_id values must be unique")
    for case in cases:
        case_id = case.get("case_id", "<missing>")
        if not isinstance(case.get("search_allowed"), bool):
            errors.append(f"{case_id}: search_allowed must be boolean")
        if case.get("ambiguity") != "low":
            errors.append(f"{case_id}: only low-ambiguity cases may be scored")
        required = set(case.get("required_actions", []))
        forbidden = set(case.get("forbidden_actions", []))
        expected_search = case.get("search_allowed") is True
        if ("search_source_material" in required) != expected_search:
            errors.append(f"{case_id}: required_actions disagrees with search_allowed")
        if not expected_search and "search_source_material" not in forbidden:
            errors.append(f"{case_id}: no-search case must forbid search_source_material")
        for fixture_field in ("snapshot_fixture_path",):
            fixture = case.get(fixture_field)
            if not fixture or not (ROOT / fixture).exists():
                errors.append(f"{case_id}: missing {fixture_field}")
    return errors


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_runtime(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative in RUNTIME_FILES:
        source = ROOT / relative
        if source.exists():
            shutil.copy2(source, destination / relative)
    for relative in RUNTIME_TREES:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    skill_source = ROOT / ".codex" / "skills" / "money-model-advisor"
    skill_target = destination / ".codex" / "skills" / "money-model-advisor"
    skill_target.mkdir(parents=True, exist_ok=True)
    for filename in ("SKILL.md", "search_request_rules.md"):
        text = (skill_source / filename).read_text(encoding="utf-8")
        text = text.replace(str(ROOT), str(destination))
        text = text.replace(
            "../../../evals/query_generation/corpus_guide_v1.json",
            "../../../reference/corpus_guide_v1.json",
        )
        (skill_target / filename).write_text(text, encoding="utf-8")
    reference_dir = destination / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "evals" / "query_generation" / "corpus_guide_v1.json",
        reference_dir / "corpus_guide_v1.json",
    )

    # The portfolio AGENTS file discusses eval assets. The acting agent needs the
    # product boundary, not evaluator documentation or filenames.
    (destination / "AGENTS.md").write_text(
        "# Money Model Advisor Runtime\n\n"
        "The human talks to an agent. The agent follows the local "
        "money-model-advisor skill and uses the CLI for deterministic state, "
        "calculation, retrieval execution, and trace recording. The agent owns "
        "semantic judgment, including whether source material is needed.\n",
        encoding="utf-8",
    )


def copy_fixture(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def prepare_business_dir(case: dict[str, Any], runtime: Path) -> Path:
    business_dir = runtime / "business"
    state_dir = business_dir / ".money-model-advisor"
    sessions_dir = state_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    copy_fixture(ROOT / case["snapshot_fixture_path"], state_dir / "business_snapshot.json")

    local_docs = case.get("local_docs_fixture_path")
    if local_docs:
        source = ROOT / local_docs
        if source.is_dir():
            shutil.copytree(source, business_dir, dirs_exist_ok=True)
        else:
            copy_fixture(source, business_dir / source.name)

    prior_sessions = case.get("prior_sessions_fixture_path")
    if prior_sessions:
        payload = json.loads((ROOT / prior_sessions).read_text(encoding="utf-8"))
        turns = payload.get("turns", [])
        for index, turn in enumerate(turns, 1):
            session = {
                "created_at": turn.get("timestamp"),
                "user_message": turn.get("user_message"),
                "assistant_message": turn.get("assistant_message"),
                "actions": turn.get("actions", []),
                "retrieval_queries": turn.get("retrieval_queries", []),
                "evidence": turn.get("evidence", []),
            }
            write_json(sessions_dir / f"prior_{index:02d}.json", session)
    return business_dir


def decision_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "context_used", "rationale"],
        "properties": {
            "decision": {"type": "string", "enum": list(DECISIONS)},
            "context_used": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["snapshot", "prior_sessions", "local_docs", "none"],
                },
            },
            "rationale": {"type": "string"},
        },
    }


def search_gate_rules() -> str:
    rules_path = ROOT / ".codex" / "skills" / "money-model-advisor" / "search_request_rules.md"
    text = rules_path.read_text(encoding="utf-8")
    try:
        return text.split("## When to search\n", 1)[1].split("\n## ", 1)[0].strip()
    except IndexError as exc:
        raise RuntimeError(f"missing 'When to search' section in {rules_path}") from exc


def load_business_context(runtime: Path, business_dir: Path, user_turn: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "python3",
            "-m",
            "money_model_architect.cli",
            "session",
            "start",
            "--business-dir",
            str(business_dir),
            "--user-message",
            user_turn,
        ],
        cwd=runtime,
        env={**os.environ, "PYTHONPATH": str(runtime / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    local_documents = {}
    for path in business_dir.rglob("*"):
        if path.is_file() and ".money-model-advisor" not in path.parts:
            local_documents[str(path.relative_to(business_dir))] = path.read_text(
                encoding="utf-8", errors="replace"
            )
    return {
        "advisor_state": payload["advisor_state"],
        "recent_turns": payload["recent_turns"],
        "local_documents": local_documents,
    }


def acting_prompt(user_turn: str, runtime: Path, business_context: dict[str, Any]) -> str:
    return f"""# Money Model Advisor Search Decision

Decide whether answering the user's request requires searching the Money Models
source material. This is the real advisor search gate, not an answer-writing task.

The current runtime rules are:

{search_gate_rules()}

1. The deterministic harness has already loaded the current advisor state and
   recent turns through the real CLI. Use the provided context as authoritative.
2. Do not run tools. Do not search the Money Models corpus. Do not answer the user's question.
   Stop once you can choose the search gate.
3. Do not inspect any path outside `{runtime}`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{json.dumps(business_context, indent=2, sort_keys=True)}
```

User request:

{user_turn}
"""


def codex_command(model: str, runtime: Path, schema_path: Path, output_path: Path) -> list[str]:
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--model",
        model,
        "--cd",
        str(runtime),
        "--sandbox",
        "workspace-write",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "--skip-git-repo-check",
        "-",
    ]


def terminate_process_group(process: subprocess.Popen[str]) -> tuple[str, str]:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        return process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        return process.communicate()


def contamination_flags(stderr: str, runtime: Path) -> list[str]:
    flags: list[str] = []
    if re.search(r"searchdecision_v\d|advisor_search_decision_cases|expected_search|search_allowed", stderr):
        flags.append("evaluation_artifact_reference")
    if str(ROOT) in stderr:
        flags.append("original_repo_reference")
    scrubbed_stderr = stderr.replace(str(runtime), "").replace(str(runtime.resolve()), "")
    if re.search(r"/(?:private/)?tmp/", scrubbed_stderr):
        flags.append("temp_path_outside_trial_runtime")
    if re.search(r"(?m)^(?:exec|apply_patch|read_mcp_resource|web_search)$", stderr):
        flags.append("unexpected_tool_call")
    # Codex logs commands as `... in /path`. Any command cwd must be the trial runtime.
    for cwd in re.findall(r"\sin\s+(/[^\n]+)$", stderr, flags=re.MULTILINE):
        try:
            Path(cwd.strip()).resolve().relative_to(runtime.resolve())
        except (ValueError, OSError):
            flags.append("command_outside_trial_runtime")
            break
    if not stderr:
        flags.append("missing_command_transcript")
    return sorted(set(flags))


def run_trial(model: str, case: dict[str, Any], output_root: Path, timeout: int) -> dict[str, Any]:
    case_id = case["case_id"]
    destination = output_root / model / case_id
    if (destination / "result.json").exists():
        return json.loads((destination / "result.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="mma-search-gate-") as temp_name:
        trial_root = Path(temp_name)
        runtime = trial_root / "runtime"
        copy_runtime(runtime)
        business_dir = prepare_business_dir(case, runtime)
        business_context = load_business_context(runtime, business_dir, case["user_turn"])
        schema_path = runtime / "decision_schema.json"
        response_path = runtime / "decision.json"
        write_json(schema_path, decision_schema())
        prompt = acting_prompt(case["user_turn"], runtime, business_context)

        started = time.perf_counter()
        process = subprocess.Popen(
            codex_command(model, runtime, schema_path, response_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=runtime,
            start_new_session=True,
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stdout, stderr = terminate_process_group(process)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        parsed: dict[str, Any] | None = None
        parse_error: str | None = None
        if response_path.exists():
            try:
                parsed = json.loads(response_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
        else:
            parse_error = "missing structured response"

        flags = contamination_flags(stderr, runtime)
        expected = "search_source_material" if case["search_allowed"] else "no_search"
        actual = parsed.get("decision") if isinstance(parsed, dict) else None
        valid = not timed_out and process.returncode == 0 and not parse_error and not flags
        result = {
            "case_id": case_id,
            "model": model,
            "expected": expected,
            "actual": actual,
            "correct": bool(valid and actual == expected),
            "valid": valid,
            "timed_out": timed_out,
            "returncode": process.returncode,
            "latency_ms": latency_ms,
            "response": parsed,
            "parse_error": parse_error,
            "contamination_flags": flags,
            "created_at": utc_now(),
        }

        destination.mkdir(parents=True, exist_ok=True)
        (destination / "acting_prompt.md").write_text(prompt, encoding="utf-8")
        (destination / "codex_stdout.txt").write_text(stdout, encoding="utf-8")
        (destination / "codex_stderr.txt").write_text(stderr, encoding="utf-8")
        write_json(destination / "decision.json", parsed)
        write_json(destination / "result.json", result)
        return result


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * quantile)))
    return ordered[index]


def render_report(cases_path: Path, results: list[dict[str, Any]], models: list[str]) -> str:
    lines = [
        "# Search-Decision Model Comparison",
        "",
        "## Method",
        "",
        f"One blind pass over {len(results) // len(models)} frozen cases per model. For each trial, the deterministic harness loaded current advisor state, recent turns, and local business documents, then the model made only the semantic search/no-search decision. Retrieval, answer generation, shell use, labels, evaluator rationales, prior trials, and evaluation documents were excluded.",
        "",
        f"Dataset SHA-256: `{sha256_file(cases_path)}`.",
        "",
        "## Results",
        "",
        "| Model | Decision accuracy | Required-search recall | No-search accuracy | Valid trials | p50 latency | p95 latency |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        rows = [row for row in results if row["model"] == model]
        valid = [row for row in rows if row["valid"]]
        required = [row for row in valid if row["expected"] == "search_source_material"]
        prohibited = [row for row in valid if row["expected"] == "no_search"]
        correct = sum(row["correct"] for row in valid)
        req_correct = sum(row["correct"] for row in required)
        no_correct = sum(row["correct"] for row in prohibited)
        latencies = [row["latency_ms"] / 1000 for row in valid]
        fmt = lambda n, d: f"{100*n/d:.1f}% ({n}/{d})" if d else "n/a"
        lines.append(
            f"| `{model}` | {fmt(correct, len(valid))} | {fmt(req_correct, len(required))} | "
            f"{fmt(no_correct, len(prohibited))} | {len(valid)}/{len(rows)} | "
            f"{percentile(latencies, .5):.1f} s | {percentile(latencies, .95):.1f} s |"
        )

    lines.extend(["", "## Cases Requiring Audit", ""])
    audit_rows = [row for row in results if not row["correct"]]
    if not audit_rows:
        lines.append("None.")
    else:
        lines.extend([
            "| Model | Case | Expected | Actual | Valid | Issue |",
            "|---|---|---|---|---:|---|",
        ])
        for row in audit_rows:
            issue = ", ".join(row["contamination_flags"]) or row["parse_error"] or ("timeout" if row["timed_out"] else "decision error")
            lines.append(
                f"| `{row['model']}` | `{row['case_id']}` | `{row['expected']}` | "
                f"`{row['actual']}` | {'yes' if row['valid'] else 'no'} | {issue} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--case-ids", nargs="+")
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    case_errors = validate_cases(cases)
    if case_errors:
        raise SystemExit("invalid search-decision suite:\n- " + "\n- ".join(case_errors))
    if args.case_ids:
        wanted = set(args.case_ids)
        cases = [case for case in cases if case["case_id"] in wanted]

    tasks = [(model, case) for model in args.models for case in cases]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {
            executor.submit(run_trial, model, case, args.output_root, args.timeout): (model, case["case_id"])
            for model, case in tasks
        }
        for future in as_completed(futures):
            model, case_id = futures[future]
            result = future.result()
            results.append(result)
            print(f"completed {model} {case_id}: valid={result['valid']} actual={result['actual']}")

    results.sort(key=lambda row: (args.models.index(row["model"]), row["case_id"]))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(args.cases, results, args.models), encoding="utf-8")
    write_json(
        args.summary_json,
        {
            "created_at": utc_now(),
            "cases_path": str(args.cases),
            "cases_sha256": sha256_file(args.cases),
            "models": args.models,
            "results": results,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
