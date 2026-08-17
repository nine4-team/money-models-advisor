#!/usr/bin/env python3
"""Run model-routing evals through the Codex CLI harness.

This runner exists because API replay is not the product harness for this
project. The advisor is agent-operated and CLI-backed, so model-tier evidence
must come from Codex agents that can inspect prepared state, run the local CLI,
and write the same trace artifacts the normal acting-agent evals score.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import capture_source_need_trace as sn_capture  # noqa: E402
import capture_tool_use_trace as tu_capture  # noqa: E402
import eval_source_need_generation as sn_eval  # noqa: E402
import eval_tool_use_judgment as tu_eval  # noqa: E402
from eval_model_routing import score_source_need, score_tool_use  # noqa: E402


DEFAULT_MODELS = ("gpt-5.5",)
TOKEN_RE = re.compile(r"tokens used\s+([0-9,]+)", re.IGNORECASE)
INFRA_FAILURE_PATTERNS = (
    "you've hit your usage limit",
    "usage limit",
    "rate limit",
    "quota",
    "authorizationrequired",
    "authorization required",
    "missing authorization header",
    "invalid_grant",
)


SUITES = {
    "source_need": {
        "cases_path": ROOT / "evals" / "advisor_source_need_cases.jsonl",
        "loader": sn_eval.load_jsonl,
        "scorer": score_source_need,
        "find_artifacts": sn_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "source_need" / "taxonomy_v2",
        "capture": sn_capture,
    },
    "tool_use": {
        "cases_path": ROOT / "evals" / "advisor_tool_use_cases.jsonl",
        "loader": tu_eval.load_jsonl,
        "scorer": score_tool_use,
        "find_artifacts": tu_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "next_action",
        "capture": tu_capture,
    },
}


class CodexInfraFailure(RuntimeError):
    """Raised when Codex CLI failed for account/quota/auth reasons."""

    def __init__(self, meta: dict[str, Any]):
        self.meta = meta
        super().__init__(
            f"{meta['model']} {meta['suite']} {meta['case_id']} failed due to "
            f"{meta.get('infra_failure_reason', 'codex infrastructure failure')}"
        )


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def decode_timeout_stream(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def detect_infra_failure(returncode: int, stderr: str) -> str | None:
    if returncode == 0:
        return None
    lowered = stderr.lower()
    for pattern in INFRA_FAILURE_PATTERNS:
        if pattern in lowered:
            return pattern
    return None


def meta_for_run_dir(run_dir: Path) -> dict[str, Any] | None:
    meta_path = run_dir / "codex_meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    run_path = run_dir / "run.json"
    if run_path.exists():
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        meta = payload.get("codex_model_meta")
        if isinstance(meta, dict):
            return meta
    return None


def is_infra_failed_run(run_dir: Path) -> bool:
    meta = meta_for_run_dir(run_dir)
    if not meta:
        return False
    if meta.get("infra_failure"):
        return True
    if not meta.get("error") and meta.get("returncode") in (None, 0):
        return False
    stderr_path = run_dir / "codex_stderr.txt"
    stderr = stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else ""
    return detect_infra_failure(int(meta.get("returncode") or 1), stderr) is not None


def run_prepare(suite: str, case: dict[str, Any], model: str, runs_dir: Path, force: bool) -> Path:
    run_dir = runs_dir / model / suite / case["case_id"]
    if run_dir.exists() and not force:
        return run_dir
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    business_dir = run_dir / ("business" if suite == "source_need" else "business_dir")
    capture = SUITES[suite]["capture"]
    if suite == "source_need":
        paths = capture.prepare_business_dir(case, business_dir)
        prompt = capture.render_acting_prompt(case, business_dir.resolve())
        draft = {
            "case_id": case["case_id"],
            "created_at": utc_now(),
            "paths": paths,
            "visible_context": {
                key: value
                for key, value in case.items()
                if key not in capture.PROMPT_HIDDEN_FIELDS and not key.startswith("_")
            },
        }
        write_json(run_dir / "run_draft.json", draft)
    else:
        stdout_dir = run_dir / "stdout"
        stderr_dir = run_dir / "stderr"
        stdout_dir.mkdir(parents=True, exist_ok=True)
        stderr_dir.mkdir(parents=True, exist_ok=True)
        paths = capture.prepare_business_dir(case, business_dir)
        prompt = capture.render_acting_prompt(case, business_dir.resolve())
        snapshot_path = business_dir / capture.STATE_DIR_NAME / capture.SNAPSHOT_FILE
        draft = {
            "case_id": case["case_id"],
            "split": case["split"],
            "phase": f"codex_model_routing_{model}",
            "created_at": utc_now(),
            "status": "prepared",
            "business_dir": rel_path(business_dir),
            "paths": paths,
            "fixtures": {
                "snapshot_fixture_path": case["snapshot_fixture_path"],
                "local_docs_fixture_path": case.get("local_docs_fixture_path"),
                "prior_sessions_fixture_path": case.get("prior_sessions_fixture_path"),
            },
            "snapshot_hash": {"start": capture.sha256_file(snapshot_path), "end": None},
            "acting_prompt_path": rel_path(run_dir / "acting_prompt.md"),
            "workflow_steps": [],
            "session_paths": [],
            "actual_actions": [],
            "final_answer_path": None,
        }
        write_json(run_dir / "run_draft.json", draft)

    prompt = append_noninteractive_requirements(suite, run_dir, prompt)
    (run_dir / "acting_prompt.md").write_text(prompt, encoding="utf-8")
    return run_dir


def append_noninteractive_requirements(suite: str, run_dir: Path, prompt: str) -> str:
    if suite == "source_need":
        completion = "\n".join(
            [
                "",
                "## Noninteractive Eval Requirement",
                "",
                f"Before your final response, you must create `{run_dir / 'run.json'}` by running:",
                "",
                "```bash",
                "PYTHONPATH=src python3 scripts/capture_source_need_trace.py complete "
                f"{run_dir} --source-search-decision <true|false> --source-need '<json-if-true>' "
                "--notes '<brief rationale>'",
                "```",
                "",
                "Your final response should only summarize the recorded decision.",
            ]
        )
    else:
        completion = "\n".join(
            [
                "",
                "## Noninteractive Eval Requirement",
                "",
                f"Before your final response, you must create `{run_dir / 'run.json'}` by running:",
                "",
                "```bash",
                "PYTHONPATH=src python3 scripts/capture_tool_use_trace.py complete "
                f"{run_dir} --workflow-steps '<json-array>' --session-paths '<json-array>' "
                "--actual-actions '<json-array>' --final-answer '<brief answer or action summary>'",
                "```",
                "",
                "Use the local CLI where the case calls for it. Do not look up expected labels.",
            ]
        )
    return prompt.rstrip() + "\n" + completion + "\n"


def codex_command(model: str, output_path: Path, agent_root: Path, writable_dir: Path) -> list[str]:
    command = [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        model,
        "--cd",
        str(agent_root),
        "--add-dir",
        str(writable_dir),
        "--sandbox",
        "workspace-write",
        "--output-last-message",
        str(output_path),
        "-",
    ]
    if not (agent_root / ".git").exists():
        command.insert(-1, "--skip-git-repo-check")
    return command


def run_codex_case(
    model: str,
    suite: str,
    case: dict[str, Any],
    runs_dir: Path,
    force: bool,
    timeout: int,
    resume_infra_failures: bool,
    agent_root: Path,
) -> Path:
    existing_run_dir = runs_dir / model / suite / case["case_id"]
    rerun_infra_failure = (
        resume_infra_failures
        and not force
        and existing_run_dir.exists()
        and is_infra_failed_run(existing_run_dir)
    )
    run_dir = run_prepare(suite, case, model, runs_dir, force=force or rerun_infra_failure)
    run_path = run_dir / "run.json"
    if run_path.exists() and not force:
        return run_path

    prompt = (run_dir / "acting_prompt.md").read_text(encoding="utf-8")
    stdout_path = run_dir / "codex_stdout.txt"
    stderr_path = run_dir / "codex_stderr.txt"
    output_path = run_dir / "codex_final.txt"
    started = time.perf_counter()
    timed_out = False
    process = subprocess.Popen(
        codex_command(model, output_path, agent_root, run_dir),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=ROOT,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=prompt, timeout=timeout)
        returncode = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        stdout = decode_timeout_stream(exc.stdout) + stdout
        stderr = decode_timeout_stream(exc.stderr) + stderr
        returncode = 124
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    token_match = TOKEN_RE.search(stdout + "\n" + stderr)
    tokens_used = int(token_match.group(1).replace(",", "")) if token_match else None
    meta = {
        "model": model,
        "suite": suite,
        "case_id": case["case_id"],
        "harness": "codex_cli_agent",
        "created_at": utc_now(),
        "latency_ms": latency_ms,
        "tokens_used_reported_by_codex": tokens_used,
        "returncode": returncode,
        "stdout_path": rel_path(stdout_path),
        "stderr_path": rel_path(stderr_path),
        "final_message_path": rel_path(output_path),
    }
    if timed_out:
        meta["error"] = "codex_exec_timeout"
        meta["timeout_seconds"] = timeout
    elif returncode != 0:
        meta["error"] = "codex_exec_failed"
    infra_failure_reason = None if timed_out else detect_infra_failure(returncode, stderr)
    if infra_failure_reason:
        meta["error"] = "codex_infra_failure"
        meta["infra_failure"] = True
        meta["infra_failure_reason"] = infra_failure_reason
    if not run_path.exists():
        meta["error"] = meta.get("error", "missing_run_json")
    write_json(run_dir / "codex_meta.json", meta)

    if meta.get("infra_failure"):
        raise CodexInfraFailure(meta)

    if not run_path.exists():
        write_json(
            run_path,
            {
                "case_id": case["case_id"],
                "completed_at": utc_now(),
                "codex_model_meta": meta,
                "source_search_decision": None if suite == "source_need" else None,
                "source_need": None if suite == "source_need" else None,
                "actual_actions": [] if suite == "tool_use" else None,
            },
        )
    else:
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        payload["codex_model_meta"] = meta
        write_json(run_path, payload)
    return run_path


def perf_summary(run_paths: list[Path]) -> dict[str, Any]:
    latencies: list[float] = []
    tokens: list[int] = []
    errors = 0
    for path in run_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        meta = payload.get("codex_model_meta") or json.loads((path.parent / "codex_meta.json").read_text(encoding="utf-8"))
        if meta.get("returncode") != 0 or meta.get("error"):
            errors += 1
        if meta.get("latency_ms") is not None:
            latencies.append(float(meta["latency_ms"]))
        if meta.get("tokens_used_reported_by_codex") is not None:
            tokens.append(int(meta["tokens_used_reported_by_codex"]))
    return {
        "requests": len(run_paths),
        "execution_errors": errors,
        "p50_latency_ms": round(statistics.median(latencies), 1) if latencies else None,
        "p95_latency_ms": round(statistics.quantiles(latencies, n=20)[18], 1)
        if len(latencies) >= 2
        else (round(latencies[0], 1) if latencies else None),
        "total_codex_reported_tokens": sum(tokens) if tokens else None,
        "avg_codex_reported_tokens": round(sum(tokens) / len(tokens), 1) if tokens else None,
    }


def fmt_pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.1f}%"


def fmt_num(value: float | None, digits: int = 1) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def render_report(
    models: list[str],
    suites: list[str],
    quality: dict[str, dict[str, dict[str, Any]]],
    perf: dict[str, dict[str, dict[str, Any]]],
    recorded: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# Codex Harness Model Routing Eval",
        "",
        "## Scope",
        "",
        "This run uses `codex exec`: each model acts through the current Money Model Advisor skill and CLI, then writes the same trace artifact scored by the tool-use golden suite. Strict case pass includes the complete expected action sequence and trace completeness; it is broader than search/no-search accuracy.",
        "",
        "## Quality",
        "",
    ]

    if "source_need" in suites:
        total = quality[models[0]]["source_need"]["total"]
        lines.extend(
            [
                f"### source_need ({total} cases)",
                "",
                "| Condition | Strict Case Pass | Search Decision | Subject Exact | Focus Concept Recall |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for model in models:
            q = quality[model]["source_need"]
            lines.append(
                f"| `{model}` via Codex CLI | {fmt_pct(q['strict_case_pass_rate'])} | {fmt_pct(q['search_decision_accuracy'])} | "
                f"{fmt_pct(q['subject_exact_match_rate'])} | {fmt_num(q['avg_focus_recall'], 3)} |"
            )
        q = recorded["source_need"]
        lines.append(
            f"| recorded acting agent reference | {fmt_pct(q['strict_case_pass_rate'])} | {fmt_pct(q['search_decision_accuracy'])} | "
            f"{fmt_pct(q['subject_exact_match_rate'])} | {fmt_num(q['avg_focus_recall'], 3)} |"
        )
        lines.append("")

    if "tool_use" in suites:
        total = quality[models[0]]["tool_use"]["total"]
        lines.extend(
            [
                f"### tool_use ({total} cases)",
                "",
                "| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for model in models:
            q = quality[model]["tool_use"]
            lines.append(
                f"| `{model}` via Codex CLI | {fmt_pct(q['strict_case_pass_rate'])} | "
                f"{fmt_num(q['avg_required_recall'], 3)} | {fmt_pct(q['forbidden_violation_rate'])} | "
                f"{fmt_pct(q['false_search_rate'])} | {fmt_pct(q['missed_search_rate'])} |"
            )
        q = recorded["tool_use"]
        lines.append(
            f"| recorded acting agent reference | {fmt_pct(q['strict_case_pass_rate'])} | "
            f"{fmt_num(q['avg_required_recall'], 3)} | {fmt_pct(q['forbidden_violation_rate'])} | "
            f"{fmt_pct(q['false_search_rate'])} | {fmt_pct(q['missed_search_rate'])} |"
        )
        lines.append("")

    lines.extend(
        [
            "## Runtime",
            "",
            "Token counts are the `tokens used` values printed by Codex CLI, not provider billing records. Because this is a ChatGPT subscription harness, dollar cost is not computed per request.",
            "",
            "| Model | Suite | p50 Latency | p95 Latency | Total Reported Tokens | Avg Reported Tokens | Execution Errors |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for model in models:
        for suite in suites:
            p = perf[model][suite]
            lines.append(
                f"| `{model}` | `{suite}` | {fmt_num(p['p50_latency_ms'], 0)} ms | {fmt_num(p['p95_latency_ms'], 0)} ms | "
                f"{p['total_codex_reported_tokens'] or '-'} | {fmt_num(p['avg_codex_reported_tokens'], 1)} | {p['execution_errors']} |"
            )

    lines.extend(["", "## Failure Modes", ""])
    for model in models:
        for suite in suites:
            modes = quality[model][suite]["failure_modes"]
            rendered = ", ".join(f"`{name}` x{count}" for name, count in modes.items()) if modes else "none"
            lines.append(f"- `{model}` via Codex CLI / `{suite}`: {rendered}")
    for suite in suites:
        modes = recorded[suite]["failure_modes"]
        rendered = ", ".join(f"`{name}` x{count}" for name, count in modes.items()) if modes else "none"
        lines.append(f"- recorded acting agent reference / `{suite}`: {rendered}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Use the strict score to diagnose the full acting workflow. For the narrower question of whether the model chose search correctly, use the focused search-decision report, which distinguishes required, prohibited, and optional-search cases.",
            "",
            "## Per-Case Failures",
            "",
            "| Model | Suite | Case | Failure Reasons |",
            "|---|---|---|---|",
        ]
    )
    any_failure = False
    for model in models:
        for suite in suites:
            for case_id, reasons in quality[model][suite]["case_failures"].items():
                any_failure = True
                lines.append(f"| `{model}` | `{suite}` | `{case_id}` | {', '.join(reasons)} |")
    if not any_failure:
        lines.append("| - | - | - | none |")
    return "\n".join(lines) + "\n"


def strip_results(block: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in block.items() if key not in ("results", "case_failures")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--suites", nargs="+", default=list(SUITES), choices=sorted(SUITES))
    parser.add_argument(
        "--tool-use-cases",
        type=Path,
        default=SUITES["tool_use"]["cases_path"],
        help="Override the tool-use case file, for example with a focused search-decision suite.",
    )
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "model_routing_codex")
    parser.add_argument(
        "--agent-root",
        type=Path,
        default=ROOT,
        help="Sanitized advisor runtime visible to acting agents. Keep golden labels out of this directory.",
    )
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "model_routing_tiering.md")
    parser.add_argument("--summary-json", type=Path, default=ROOT / "evals" / "reports" / "model_routing_tiering_summary.json")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, help="Run only the first N cases per suite for smoke testing.")
    parser.add_argument("--case-ids", nargs="+", help="Run only these case IDs after suite filtering.")
    parser.add_argument(
        "--resume-infra-failures",
        action="store_true",
        help="Rerun existing cases only when their Codex metadata shows quota/auth infrastructure failure.",
    )
    args = parser.parse_args()

    suite_paths = {
        suite: args.tool_use_cases if suite == "tool_use" else SUITES[suite]["cases_path"]
        for suite in args.suites
    }
    suite_cases = {suite: SUITES[suite]["loader"](suite_paths[suite]) for suite in args.suites}
    if args.case_ids is not None:
        requested = set(args.case_ids)
        suite_cases = {
            suite: [case for case in cases if case["case_id"] in requested]
            for suite, cases in suite_cases.items()
        }
        found = {case["case_id"] for cases in suite_cases.values() for case in cases}
        missing = sorted(requested - found)
        if missing:
            parser.error(f"--case-ids not found in selected suites: {', '.join(missing)}")
    if args.limit is not None:
        suite_cases = {suite: cases[: args.limit] for suite, cases in suite_cases.items()}

    tasks = [
        (model, suite, case)
        for model in args.models
        for suite in args.suites
        for case in suite_cases[suite]
    ]
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {}
        for model, suite, case in tasks:
            print(f"queued {model} {suite} {case['case_id']}", file=sys.stderr)
            future = executor.submit(
                run_codex_case,
                model,
                suite,
                case,
                args.runs_dir,
                args.force,
                args.timeout,
                args.resume_infra_failures,
                args.agent_root,
            )
            futures[future] = (model, suite, case["case_id"])
        for future in as_completed(futures):
            model, suite, case_id = futures[future]
            try:
                future.result()
            except CodexInfraFailure as exc:
                print(
                    "aborting after Codex infrastructure failure: "
                    f"{json.dumps(exc.meta, sort_keys=True)}",
                    file=sys.stderr,
                )
                for pending in futures:
                    pending.cancel()
                return 2
            print(f"completed {model} {suite} {case_id}", file=sys.stderr)

    quality: dict[str, dict[str, dict[str, Any]]] = {}
    perf: dict[str, dict[str, dict[str, Any]]] = {}
    for model in args.models:
        quality[model] = {}
        perf[model] = {}
        for suite in args.suites:
            suite_dir = args.runs_dir / model / suite
            artifacts = SUITES[suite]["find_artifacts"](suite_dir)
            quality[model][suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)
            perf[model][suite] = perf_summary(sorted(suite_dir.rglob("run.json")))

    recorded: dict[str, dict[str, Any]] = {}
    for suite in args.suites:
        artifacts = SUITES[suite]["find_artifacts"](SUITES[suite]["recorded_runs_dir"])
        recorded[suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)

    report = render_report(args.models, args.suites, quality, perf, recorded)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    summary = {
        "created_at": utc_now(),
        "harness": "codex_cli_agent",
        "models": args.models,
        "suites": args.suites,
        "quality": {model: {suite: strip_results(quality[model][suite]) for suite in args.suites} for model in args.models},
        "performance": perf,
        "recorded_acting_agent_reference": {suite: strip_results(recorded[suite]) for suite in args.suites},
    }
    write_json(args.summary_json, summary)
    print(json.dumps({"report": rel_path(args.report), "summary": rel_path(args.summary_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
