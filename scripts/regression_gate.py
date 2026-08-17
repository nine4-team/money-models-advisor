#!/usr/bin/env python3
"""Run the stable, offline Money Model Advisor regression gate."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]


PYTHON = sys.executable
CHECKS = (
    Check("Unit tests", (PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v")),
    Check("Local retrieval smoke", (PYTHON, "scripts/eval_smoke.py")),
    Check(
        "Tool-use traces",
        (PYTHON, "scripts/eval_tool_use_judgment.py", "--require-all-pass"),
    ),
    Check(
        "Source-event traces",
        (PYTHON, "scripts/eval_source_event_traces.py", "--require-all-pass"),
    ),
    Check(
        "Calculation traces",
        (PYTHON, "scripts/eval_calculation_trace_events.py"),
    ),
    Check(
        "Answer quality",
        (PYTHON, "scripts/eval_advisor_answer_quality.py", "--require-all-pass"),
    ),
    Check(
        "Narrative evidence",
        (PYTHON, "scripts/render_narrative_evidence.py", "--check"),
    ),
    Check("Patch hygiene", ("git", "diff", "--check")),
)


def main() -> int:
    env = os.environ.copy()
    src = str(ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing_pythonpath else os.pathsep.join((src, existing_pythonpath))

    started = time.monotonic()
    print(f"Running {len(CHECKS)} stable offline checks from {ROOT}", flush=True)
    for index, check in enumerate(CHECKS, 1):
        print(f"\n[{index}/{len(CHECKS)}] {check.name}", flush=True)
        completed = subprocess.run(check.command, cwd=ROOT, env=env, check=False)
        if completed.returncode:
            print(
                f"\nREGRESSION GATE FAILED: {check.name} exited {completed.returncode}",
                file=sys.stderr,
                flush=True,
            )
            return completed.returncode

    elapsed = time.monotonic() - started
    print(f"\nREGRESSION GATE PASSED: {len(CHECKS)}/{len(CHECKS)} checks in {elapsed:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
