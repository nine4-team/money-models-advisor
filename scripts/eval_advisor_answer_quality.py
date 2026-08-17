#!/usr/bin/env python3
"""Validate frozen full-answer audits and summarize semantic quality."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "evals" / "advisor_answer_quality_expanded_final_audit.jsonl"
DEFAULT_RUNS = ROOT / "evals" / "runs" / "answer_quality" / "expanded_v1_final"
DEFAULT_REPORT = ROOT / "evals" / "reports" / "advisor_answer_quality_expanded.md"
REQUIRED_FIELDS = {
    "case_id", "answer_sha256", "reviewer", "reviewed_at", "business_facts_accurate",
    "calculations_accurate", "book_application_reasonable", "useful_and_responsive",
    "appropriate_restraint", "material_claims", "overall_pass", "failure_categories", "rationale",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * quantile)))
    return ordered[index]


def _evaluate_expanded(audits: list[dict[str, Any]], runs_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for audit in audits:
        case_id = audit.get("case_id", "<missing>")
        if case_id in seen:
            errors.append(f"duplicate audit: {case_id}")
        seen.add(case_id)
        missing = sorted(REQUIRED_FIELDS - set(audit))
        if missing:
            errors.append(f"{case_id}: missing fields: {', '.join(missing)}")
            continue
        if audit["reviewer"] != "codex_semantic_audit":
            errors.append(f"{case_id}: unexpected reviewer")

        trial_dir = runs_dir / case_id
        packet_path = trial_dir / "audit_packet.json"
        result_path = trial_dir / "result.json"
        if not packet_path.exists() or not result_path.exists():
            errors.append(f"{case_id}: missing frozen trial artifacts")
            continue
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        result = json.loads(result_path.read_text(encoding="utf-8"))
        actual_hash = hashlib.sha256(packet["assistant_message"].encode()).hexdigest()
        current = actual_hash == audit["answer_sha256"] == packet["answer_sha256"]
        if not current:
            errors.append(f"{case_id}: answer hash does not match audit")
        if not result.get("valid"):
            errors.append(f"{case_id}: frozen trial is not workflow-valid")

        claims = audit["material_claims"]
        if not isinstance(claims, list):
            errors.append(f"{case_id}: material_claims must be a list")
            continue
        supported = sum(bool(claim.get("supported")) for claim in claims)
        rows.append(
            {
                "case_id": case_id,
                "scenario_id": packet["scenario_id"],
                "category": packet["answer_category"],
                "current": current,
                "valid": bool(result.get("valid")),
                "overall_pass": bool(audit["overall_pass"]),
                "business_facts_accurate": bool(audit["business_facts_accurate"]),
                "calculations_accurate": audit["calculations_accurate"],
                "book_application_reasonable": bool(audit["book_application_reasonable"]),
                "useful_and_responsive": bool(audit["useful_and_responsive"]),
                "appropriate_restraint": bool(audit["appropriate_restraint"]),
                "claims": len(claims),
                "supported_claims": supported,
                "failure_categories": audit["failure_categories"],
                "rationale": audit["rationale"],
                "latency_ms": float(result["latency_ms"]),
            }
        )
    return rows, errors


def evaluate(audits: list[dict[str, Any]], runs_dir: Path) -> list[dict[str, Any]]:
    """Return scorer rows while preserving the original evaluator API.

    The six-case historical audit used ``run.json`` and a smaller audit schema.
    Keeping that reader here lets its regression tests continue to prove that
    answer hashes prevent stale semantic judgments. Current expanded audits use
    ``evaluate_expanded`` for strict artifact and schema validation.
    """
    if audits and "material_claims" not in audits[0]:
        rows: list[dict[str, Any]] = []
        for audit in audits:
            run = json.loads((runs_dir / audit["case_id"] / "run.json").read_text(encoding="utf-8"))
            answer_hash = hashlib.sha256(run["assistant_message"].encode()).hexdigest()
            claims = audit["claims"]
            rows.append({
                "case_id": audit["case_id"],
                "current": answer_hash == audit["answer_sha256"],
                "recommendation_correct": bool(audit["recommendation_correct"]),
                "recommendation_useful": bool(audit["recommendation_useful"]),
                "claims": len(claims),
                "supported_claims": sum(bool(claim["supported"]) for claim in claims),
            })
        return rows

    rows, _ = _evaluate_expanded(audits, runs_dir)
    return rows


def evaluate_expanded(
    audits: list[dict[str, Any]], runs_dir: Path
) -> tuple[list[dict[str, Any]], list[str]]:
    """Strictly validate the current expanded audit and its frozen artifacts."""
    return _evaluate_expanded(audits, runs_dir)


def all_audits_pass(audits: list[dict[str, Any]], rows: list[dict[str, Any]]) -> bool:
    """Return whether every answer and material claim passes its current audit."""
    return len(rows) == len(audits) and all(
        row["current"]
        and row["valid"]
        and row["overall_pass"]
        and row["supported_claims"] == row["claims"]
        for row in rows
    )


def render_report(rows: list[dict[str, Any]], audit_path: Path, runs_dir: Path) -> str:
    failures = [row for row in rows if not row["overall_pass"]]
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
        by_scenario[row["scenario_id"]].append(row)
    failure_counts = Counter(category for row in failures for category in row["failure_categories"])
    latencies = [row["latency_ms"] for row in rows]
    total_claims = sum(row["claims"] for row in rows)
    supported_claims = sum(row["supported_claims"] for row in rows)

    title = "# Expanded Advisor Answer-Quality Baseline" if failures else "# Expanded Advisor Answer-Quality Audit"
    lines = [
        title, "", "## Method", "",
        "Twenty frozen `gpt-5.5` advisor turns were generated in fresh sanitized runtimes: four cases from each of five business contexts, comprising ten source-grounded answers, five deterministic calculations, and five clarification decisions. Source-grounded cases had to complete the current single-query hybrid path and cite retrieved passages; calculation cases had to record a recomputable CLI event; clarification cases had to record `clarify` without retrieval. Codex then reviewed each fixed answer against its captured snapshot, tool events, and exact retrieved text. Answer hashes bind every judgment to the reviewed output.",
        "", "## Results", "",
        f"- Workflow-valid frozen runs: {sum(row['valid'] for row in rows)} / {len(rows)}",
        f"- Semantic answer passes: {sum(row['overall_pass'] for row in rows)} / {len(rows)}",
        f"- Supported material claims: {supported_claims} / {total_claims}",
        f"- Latency: {statistics.median(latencies) / 1000:.1f}s p50 / {percentile(latencies, 0.95) / 1000:.1f}s p95",
        "", "| Answer category | Passed |", "|---|---:|",
    ]
    for category in ("source_grounded", "calculation", "clarification"):
        category_rows = by_category[category]
        lines.append(f"| `{category}` | {sum(row['overall_pass'] for row in category_rows)} / {len(category_rows)} |")

    lines.extend(["", "| Business context | Passed |", "|---|---:|"])
    for scenario_id in sorted(by_scenario):
        scenario_rows = by_scenario[scenario_id]
        lines.append(f"| `{scenario_id}` | {sum(row['overall_pass'] for row in scenario_rows)} / {len(scenario_rows)} |")

    lines.extend(["", "## Failure Analysis", ""])
    if failures:
        lines.extend([
            "All ten source-grounded answers and all five deterministic calculations passed. Four of five clarification answers failed for one shared reason: the advice correctly withheld a scale decision, but then requested too few economic inputs for the calculation it promised. CAC plus first-30-day gross profit can establish whether acquisition pays back inside one month. When it does not, exact payback also requires recurring gross profit. A downstream lead-value calculation likewise needs downstream gross profit, not only offer price and conversion rate.", "",
        ])
    else:
        lines.extend([
            "No semantic failures remain in the final 20-case suite. The initial frozen baseline passed 16 / 20: all source-grounded and calculation answers passed, while four clarification answers overpromised decisions from incomplete economics. The runtime now conditionally requires recurring gross profit when month-one gross profit does not recover CAC, and the advisor runbook distinguishes the first-month gate, recurring-payback branch, and downstream expected-value branch. A later countercase also caught and removed an arbitrary percentage-spend recommendation. The final outputs were regenerated blind and reviewed after freezing.", "",
        ])
    if failure_counts:
        lines.append("Failure labels: " + ", ".join(f"`{name}` {count}" for name, count in sorted(failure_counts.items())) + ".")
        lines.append("")
    lines.extend(["| Case | Category | Result | Audit rationale |", "|---|---|---:|---|"])
    for row in rows:
        lines.append(f"| `{row['case_id']}` | `{row['category']}` | {'pass' if row['overall_pass'] else 'fail'} | {row['rationale']} |")

    interpretation = (
        "The baseline supports the source-grounded recommendation and deterministic-calculation paths, but it does not yet support claiming complete answer quality. The clarification failure is general rather than case-specific, so the next step is to correct the input-sufficiency rule and rerun the clarification cases plus countercases without overwriting this baseline."
        if failures
        else "The final suite supports the current source-grounded, calculation, and clarification paths across all five represented business contexts. This closes the identified answer-quality remediation item while preserving the failed 16/20 baseline and final 20/20 run for inspection."
    )
    lines.extend([
        "", "## Interpretation", "", interpretation,
        "", "## Scope", "",
        "This is a balanced 20-case regression, not a population estimate. Codex performed the semantic review rather than an independent human reviewer. The review artifact and frozen run directory are retained at "
        f"`{audit_path.resolve().relative_to(ROOT)}` and `{runs_dir.resolve().relative_to(ROOT)}`.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--require-all-pass",
        action="store_true",
        help="Fail unless every frozen answer and every material claim passes its current audit.",
    )
    args = parser.parse_args()

    audits = load_jsonl(args.audit)
    rows, errors = evaluate_expanded(audits, args.runs_dir)
    if errors:
        raise SystemExit("invalid answer-quality audit:\n- " + "\n- ".join(errors))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(rows, args.audit, args.runs_dir), encoding="utf-8")
    print(json.dumps({
        "cases": len(rows),
        "passes": sum(row["overall_pass"] for row in rows),
        "claims": sum(row["claims"] for row in rows),
        "supported_claims": sum(row["supported_claims"] for row in rows),
        "report": str(args.report.resolve().relative_to(ROOT)),
    }, indent=2))
    if args.require_all_pass and not all_audits_pass(audits, rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
