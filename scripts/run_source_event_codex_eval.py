#!/usr/bin/env python3
"""Run the six source-event cases through isolated Codex CLI acting agents."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import capture_source_event_trace as capture


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_case(case: dict, run_dir: Path, force: bool) -> None:
    if run_dir.exists() and force:
        shutil.rmtree(run_dir)
    if run_dir.exists():
        return
    run_dir.mkdir(parents=True)
    business_dir = run_dir / "business"
    paths = capture.prepare_business_dir(case, business_dir)
    visible = {key: value for key, value in case.items() if key not in capture.PROMPT_HIDDEN_FIELDS and not key.startswith("_")}
    prompt = capture.render_acting_prompt(case, business_dir.resolve()).rstrip() + "\n\n" + "\n".join([
        "## Noninteractive completion requirement",
        "",
        "Do not edit project source files. Work only inside the prepared business and run directories.",
        "After `session finish`, use the returned `session_path` to create the eval artifact:",
        "",
        "```bash",
        f"PYTHONPATH=src python3 scripts/capture_source_event_trace.py complete {run_dir.resolve()} --session-path <session_path> --notes 'blind Codex acting-agent run'",
        "```",
        "",
        "You must create `run.json` before returning. Your final response should only summarize the recorded action.",
        "",
    ])
    (run_dir / "acting_prompt.md").write_text(prompt, encoding="utf-8")
    write_json(run_dir / "run_draft.json", {
        "case_id": case["case_id"],
        "created_at": utc_now(),
        "paths": paths,
        "visible_context": visible,
    })


def run_case(case: dict, args: argparse.Namespace) -> dict:
    run_dir = args.runs_dir / case["case_id"]
    prepare_case(case, run_dir, args.force)
    run_path = run_dir / "run.json"
    if run_path.exists() and not args.force:
        return {"case_id": case["case_id"], "status": "reused", "run": str(run_path)}
    prompt = (run_dir / "acting_prompt.md").read_text(encoding="utf-8")
    command = [
        "codex", "--ask-for-approval", "never", "exec", "--model", args.model,
        "--cd", str(ROOT), "--sandbox", "workspace-write",
        "--output-last-message", str(run_dir / "codex_final.txt"), "-",
    ]
    started = time.perf_counter()
    completed = subprocess.run(command, input=prompt, text=True, cwd=ROOT, capture_output=True, timeout=args.timeout)
    (run_dir / "codex_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (run_dir / "codex_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    meta = {
        "case_id": case["case_id"],
        "model": args.model,
        "harness": "codex_cli_agent",
        "created_at": utc_now(),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "returncode": completed.returncode,
        "run_created": run_path.exists(),
    }
    write_json(run_dir / "codex_meta.json", meta)
    return {"case_id": case["case_id"], "status": "completed" if run_path.exists() else "failed", **meta}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_source_event_cases.jsonl")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "source_events" / "search_request_v1")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--max-workers", type=int, default=2)
    args = parser.parse_args()
    cases = capture.load_jsonl(args.cases)
    if args.case_id:
        selected = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in selected]
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {executor.submit(run_case, case, args): case["case_id"] for case in cases}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    return 0 if all(result["status"] in {"completed", "reused"} for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
