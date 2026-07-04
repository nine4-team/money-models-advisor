#!/usr/bin/env python3
"""Score a within-Claude model-tier sweep (Opus / Sonnet / Haiku) on the two
model-routing golden suites.

This reuses the exact scorers and golden cases from the gpt-5.5 Codex baseline
and the Opus harness run. Every tier acted through the same CLI-backed harness
(one Claude Code subagent per case, reading only the prepared acting prompt and
the case's own saved state), and every tier is scored here by the identical
deterministic scorers. No model is called from this script; it only reads the
`run.json` artifacts already on disk.

The point of the sweep is the tiering question the JD asks about model routing:
can a cheaper Claude tier hold the semantic-planning role, and where does it slip?
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import eval_source_need_generation as sn_eval  # noqa: E402
import eval_tool_use_judgment as tu_eval  # noqa: E402
from eval_model_routing import score_source_need, score_tool_use  # noqa: E402


SUITES = {
    "source_need": {
        "cases_path": ROOT / "evals" / "advisor_source_need_cases.jsonl",
        "loader": sn_eval.load_jsonl,
        "scorer": score_source_need,
        "find_artifacts": sn_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "source_need" / "taxonomy_v2",
    },
    "tool_use": {
        "cases_path": ROOT / "evals" / "advisor_tool_use_cases.jsonl",
        "loader": tu_eval.load_jsonl,
        "scorer": score_tool_use,
        "find_artifacts": tu_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "next_action",
    },
}

# label -> runs dir holding <suite>/<case_id>/run.json
TIERS = {
    "claude-opus-4-8": ROOT / "evals" / "runs" / "model_routing_opus" / "claude-opus-4-8",
    "claude-sonnet-5": ROOT / "evals" / "runs" / "model_routing_tiers" / "claude-sonnet-5",
    "claude-haiku-4-5": ROOT / "evals" / "runs" / "model_routing_tiers" / "claude-haiku-4-5",
}


def strip(block: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in block.items() if k not in ("results", "case_failures")}


def main() -> int:
    suite_cases = {s: SUITES[s]["loader"](SUITES[s]["cases_path"]) for s in SUITES}

    quality: dict[str, dict[str, Any]] = {}
    for label, run_dir in TIERS.items():
        quality[label] = {}
        for suite in SUITES:
            suite_dir = run_dir / suite
            artifacts = SUITES[suite]["find_artifacts"](suite_dir)
            quality[label][suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)

    reference: dict[str, Any] = {}
    for suite in SUITES:
        artifacts = SUITES[suite]["find_artifacts"](SUITES[suite]["recorded_runs_dir"])
        reference[suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)

    out = {
        "harness": "claude_code_subagent_per_case",
        "tiers": list(TIERS),
        "suites": list(SUITES),
        "quality": {m: {s: strip(quality[m][s]) for s in SUITES} for m in TIERS},
        "reference": {s: strip(reference[s]) for s in SUITES},
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
