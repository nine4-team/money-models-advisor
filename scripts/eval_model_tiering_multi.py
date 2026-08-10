#!/usr/bin/env python3
"""Score the within-Claude tier sweep across repeated runs and report per-run
strict case pass plus the mean.

Same scorers and golden cases as the gpt-5.5 / Opus baselines. Every tier acted
through the identical CLI-backed harness (one Claude Code subagent per case);
this script only reads the run.json artifacts on disk and scores them. No model
is called.

Run-1 dirs: Sonnet/Haiku from model_routing_tiers, Opus from model_routing_opus.
Run-2/run-3 dirs: model_tiering/run2/<model>, model_tiering/run3/<model>.
All three tiers now have K=3 runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import eval_source_need_generation as sn_eval  # noqa: E402
import eval_tool_use_judgment as tu_eval  # noqa: E402
from eval_model_routing import score_source_need, score_tool_use  # noqa: E402

SUITES = {
    "source_need": (
        ROOT / "evals" / "advisor_source_need_cases.jsonl",
        sn_eval.load_jsonl,
        score_source_need,
        sn_eval.find_run_artifacts,
        ROOT / "evals" / "runs" / "source_need" / "taxonomy_v2",
    ),
    "tool_use": (
        ROOT / "evals" / "advisor_tool_use_cases.jsonl",
        tu_eval.load_jsonl,
        score_tool_use,
        tu_eval.find_run_artifacts,
        ROOT / "evals" / "runs" / "next_action",
    ),
}

RUN1 = ROOT / "evals" / "runs" / "model_routing_tiers"
RUN2 = ROOT / "evals" / "runs" / "model_tiering" / "run2"
RUN3 = ROOT / "evals" / "runs" / "model_tiering" / "run3"
OPUS1 = ROOT / "evals" / "runs" / "model_routing_opus" / "claude-opus-4-8"

# tier -> ordered list of run dirs (each holds <suite>/<case>/run.json)
TIERS = {
    "claude-opus-4-8": [OPUS1, RUN2 / "claude-opus-4-8", RUN3 / "claude-opus-4-8"],
    "claude-sonnet-5": [RUN1 / "claude-sonnet-5", RUN2 / "claude-sonnet-5", RUN3 / "claude-sonnet-5"],
    "claude-haiku-4-5": [RUN1 / "claude-haiku-4-5", RUN2 / "claude-haiku-4-5", RUN3 / "claude-haiku-4-5"],
}

KEYS = {
    "source_need": ["strict_case_pass_rate", "search_decision_accuracy", "subject_exact_match_rate", "avg_focus_recall"],
    "tool_use": ["strict_case_pass_rate", "avg_required_recall", "forbidden_violation_rate", "false_search_rate", "missed_search_rate"],
}


def score_run(run_dir: Path):
    out = {}
    for suite, (cases_path, loader, scorer, find, _ref) in SUITES.items():
        suite_dir = run_dir / suite
        if not suite_dir.exists():
            out[suite] = None
            continue
        cases = loader(cases_path)
        res = scorer(cases, find(suite_dir))
        out[suite] = {k: res.get(k) for k in KEYS[suite]} | {"failure_modes": res.get("failure_modes", {}), "scored": res.get("scored")}
    return out


def main() -> int:
    report = {}
    for tier, run_dirs in TIERS.items():
        runs = [score_run(d) for d in run_dirs]
        per_suite = {}
        for suite in SUITES:
            present = [r[suite] for r in runs if r[suite] is not None and r[suite].get("strict_case_pass_rate") is not None]
            if not present:
                per_suite[suite] = None
                continue
            avg = {k: round(mean(r[k] for r in present), 4) for k in KEYS[suite]}
            per_suite[suite] = {
                "n_runs": len(present),
                "per_run_strict": [round(r["strict_case_pass_rate"], 4) for r in present],
                "mean": avg,
                "failure_modes_by_run": [r["failure_modes"] for r in present],
            }
        report[tier] = per_suite
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
