#!/usr/bin/env python3
"""Score next-action classification traces for the Money Model Advisor.

This script validates the product-behavior case set and scores saved run
artifacts when they exist. It does not call external model APIs and it does not
run an agent. Agent execution should write `run.json` files under
`evals/runs/next_action/...`; this script turns those traces into an auditable
report.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

ACTION_TAXONOMY = {
    "clarify",
    "update_snapshot",
    "read_snapshot",
    "read_logs",
    "inspect_local_docs",
    "calculate",
    "diagnose",
    "search_source_material",
    "compose_answer_from_state",
    "answer_without_tool",
}

CONFIDENCE_VALUES = {"direct", "inferred", "missing"}

TOOL_LIKE_ACTIONS = {
    "update_snapshot",
    "read_snapshot",
    "read_logs",
    "inspect_local_docs",
    "calculate",
    "diagnose",
    "search_source_material",
}

REQUIRED_CASE_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "turn_type",
    "conversation_context",
    "snapshot_fixture_path",
    "local_docs_fixture_path",
    "prior_sessions_fixture_path",
    "user_turn",
    "required_actions",
    "allowed_actions",
    "forbidden_actions",
    "expected_first_action",
    "search_allowed",
    "expected_mutation",
    "label_rationale",
    "ambiguity",
    "severity_if_wrong",
}


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    split: str
    turn_type: str
    run_path: Path | None
    status: str
    first_action_correct: bool | None
    required_recall: float | None
    forbidden_violation: bool | None
    false_search: bool | None
    missed_search: bool | None
    full_sequence_pass: bool | None
    trace_complete: bool | None
    actual_actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            record["_line_number"] = line_number
            records.append(record)
    return records


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for case in cases:
        case_ref = f"{case.get('case_id', '<missing>')} line {case.get('_line_number', '?')}"
        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_ref}: missing fields: {', '.join(sorted(missing))}")

        case_id = case.get("case_id")
        if case_id in seen:
            errors.append(f"{case_ref}: duplicate case_id")
        seen.add(case_id)

        for field in ("required_actions", "allowed_actions", "forbidden_actions"):
            actions = case.get(field)
            if not isinstance(actions, list):
                errors.append(f"{case_ref}: {field} must be a list")
                continue
            unknown = sorted(set(actions) - ACTION_TAXONOMY)
            if unknown:
                errors.append(f"{case_ref}: unknown {field}: {', '.join(unknown)}")

        first = case.get("expected_first_action")
        if first not in ACTION_TAXONOMY:
            errors.append(f"{case_ref}: unknown expected_first_action: {first}")

        required = set(case.get("required_actions", []))
        allowed = set(case.get("allowed_actions", []))
        forbidden = set(case.get("forbidden_actions", []))
        if required & forbidden:
            errors.append(
                f"{case_ref}: action cannot be both required and forbidden: "
                f"{', '.join(sorted(required & forbidden))}"
            )
        if allowed & forbidden:
            errors.append(
                f"{case_ref}: action cannot be both allowed and forbidden: "
                f"{', '.join(sorted(allowed & forbidden))}"
            )

        search_allowed = case.get("search_allowed")
        if search_allowed is not True and "search_source_material" in required:
            errors.append(f"{case_ref}: search is required but search_allowed is not true")
        if search_allowed is False and "search_source_material" not in forbidden:
            errors.append(f"{case_ref}: search_allowed is false but search is not forbidden")

        for field in ("snapshot_fixture_path", "local_docs_fixture_path", "prior_sessions_fixture_path"):
            value = case.get(field)
            if value is None:
                continue
            fixture_path = ROOT / value
            if not fixture_path.exists():
                errors.append(f"{case_ref}: fixture does not exist: {value}")

    return errors


def find_run_artifacts(runs_dir: Path) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    if not runs_dir.exists():
        return artifacts

    for path in sorted(runs_dir.rglob("run.json")):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        case_id = run.get("case_id")
        if isinstance(case_id, str):
            artifacts[case_id] = path
    return artifacts


def extract_actual_actions(run: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    raw_actions = run.get("actual_actions", [])
    actions: list[str] = []
    failures: list[str] = []
    trace_complete = True

    if not isinstance(raw_actions, list):
        return [], ["actual_actions_not_list"], False

    if not raw_actions:
        return [], ["missing_actual_actions"], False

    for index, item in enumerate(raw_actions):
        if not isinstance(item, dict):
            failures.append(f"actual_actions[{index}]_not_object")
            trace_complete = False
            continue

        action = item.get("action")
        confidence = item.get("confidence")

        if action not in ACTION_TAXONOMY:
            failures.append(f"unknown_action:{action}")
            trace_complete = False
            continue

        if confidence not in CONFIDENCE_VALUES:
            failures.append(f"unknown_confidence:{confidence}")
            trace_complete = False
        elif confidence == "missing":
            failures.append(f"missing_evidence:{action}")
            trace_complete = False

        if confidence == "direct" and action in TOOL_LIKE_ACTIONS:
            if not item.get("evidence_type"):
                failures.append(f"missing_evidence_type:{action}")
                trace_complete = False
            if not item.get("evidence_ref"):
                failures.append(f"missing_evidence_ref:{action}")
                trace_complete = False

        actions.append(action)

    return actions, failures, trace_complete


def score_case(case: dict[str, Any], run_path: Path | None) -> CaseResult:
    if run_path is None:
        return CaseResult(
            case_id=case["case_id"],
            split=case["split"],
            turn_type=case["turn_type"],
            run_path=None,
            status="not_run",
            first_action_correct=None,
            required_recall=None,
            forbidden_violation=None,
            false_search=None,
            missed_search=None,
            full_sequence_pass=None,
            trace_complete=None,
            actual_actions=(),
            failure_reasons=(),
        )

    run = json.loads(run_path.read_text(encoding="utf-8"))
    actual_actions, trace_failures, trace_complete = extract_actual_actions(run)
    actual_set = set(actual_actions)
    required = set(case["required_actions"])
    forbidden = set(case["forbidden_actions"])

    first_action_correct = bool(actual_actions) and actual_actions[0] == case["expected_first_action"]
    required_recall = len(required & actual_set) / len(required) if required else 1.0
    forbidden_hits = forbidden & actual_set
    forbidden_violation = bool(forbidden_hits)
    false_search = "search_source_material" in actual_set and "search_source_material" in forbidden
    missed_search = "search_source_material" in required and "search_source_material" not in actual_set
    full_sequence_pass = required_recall == 1.0 and not forbidden_violation and trace_complete

    failures = list(trace_failures)
    if not first_action_correct:
        failures.append("wrong_first_action")
    if required_recall < 1.0:
        missing = sorted(required - actual_set)
        failures.append(f"missing_required:{','.join(missing)}")
    if forbidden_violation:
        failures.append(f"forbidden_action:{','.join(sorted(forbidden_hits))}")
    if false_search:
        failures.append("false_search")
    if missed_search:
        failures.append("missed_search")

    return CaseResult(
        case_id=case["case_id"],
        split=case["split"],
        turn_type=case["turn_type"],
        run_path=run_path,
        status="scored",
        first_action_correct=first_action_correct,
        required_recall=required_recall,
        forbidden_violation=forbidden_violation,
        false_search=false_search,
        missed_search=missed_search,
        full_sequence_pass=full_sequence_pass,
        trace_complete=trace_complete,
        actual_actions=tuple(actual_actions),
        failure_reasons=tuple(failures),
    )


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{(numerator / denominator) * 100:.1f}%"


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def summarize_scored(results: list[CaseResult]) -> dict[str, Any]:
    scored = [result for result in results if result.status == "scored"]
    if not scored:
        return {"scored_count": 0}

    recall_values = [result.required_recall for result in scored if result.required_recall is not None]
    return {
        "scored_count": len(scored),
        "first_action_accuracy": pct(
            sum(1 for result in scored if result.first_action_correct is True), len(scored)
        ),
        "full_sequence_pass_rate": pct(
            sum(1 for result in scored if result.full_sequence_pass is True), len(scored)
        ),
        "forbidden_violation_rate": pct(
            sum(1 for result in scored if result.forbidden_violation is True), len(scored)
        ),
        "false_search_rate": pct(sum(1 for result in scored if result.false_search is True), len(scored)),
        "missed_search_rate": pct(sum(1 for result in scored if result.missed_search is True), len(scored)),
        "trace_completeness": pct(sum(1 for result in scored if result.trace_complete is True), len(scored)),
        "avg_required_recall": None if average(recall_values) is None else f"{average(recall_values):.3f}",
    }


def render_report(cases: list[dict[str, Any]], results: list[CaseResult], validation_errors: list[str]) -> str:
    lines: list[str] = [
        "# Advisor Tool-Use Judgment Eval",
        "",
        "## Hypothesis",
        "",
        "The skill-guided advisor should choose the correct next action or action sequence before answering: read saved state, inspect logs, inspect local docs, calculate, diagnose, search source material, clarify, update memory, or answer without tools.",
        "",
        "## Dataset Slice",
        "",
        f"- Cases: {len(cases)}",
        f"- Splits: {dict(sorted(Counter(case['split'] for case in cases).items()))}",
        f"- Turn types: {dict(sorted(Counter(case['turn_type'] for case in cases).items()))}",
        "",
        "These are product-behavior cases. Harness/operability questions about eval terminology should live in a separate file and should not count toward headline advisor-quality metrics.",
        "",
        "## Validation",
        "",
    ]

    if validation_errors:
        lines.append(f"- Status: failed ({len(validation_errors)} issues)")
        for error in validation_errors:
            lines.append(f"- {error}")
    else:
        lines.append("- Status: passed")

    scored_summary = summarize_scored(results)
    scored_count = scored_summary["scored_count"]

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "- first-action accuracy",
            "- required-action recall",
            "- forbidden-action violation rate",
            "- false-search rate",
            "- missed-search rate",
            "- full-sequence pass rate",
            "- trace completeness",
            "",
            "## Results",
            "",
        ]
    )

    if scored_count == 0:
        lines.extend(
            [
                "No `run.json` artifacts were found, so this report currently covers case inventory and validation only.",
                "",
                "Next step: run the skill-guided agent workflow for each case in isolated eval directories and write `run.json` traces under `evals/runs/next_action/`.",
            ]
        )
    else:
        lines.extend(
            [
                f"- Scored cases: {scored_count}",
                f"- First-action accuracy: {scored_summary['first_action_accuracy']}",
                f"- Average required-action recall: {scored_summary['avg_required_recall']}",
                f"- Full-sequence pass rate: {scored_summary['full_sequence_pass_rate']}",
                f"- Forbidden-action violation rate: {scored_summary['forbidden_violation_rate']}",
                f"- False-search rate: {scored_summary['false_search_rate']}",
                f"- Missed-search rate: {scored_summary['missed_search_rate']}",
                f"- Trace completeness: {scored_summary['trace_completeness']}",
            ]
        )

    lines.extend(["", "## Case Table", "", "| Case | Split | Turn Type | Status | Actual Actions | Failures |", "|---|---|---|---|---|---|"])
    for result in results:
        actual = ", ".join(result.actual_actions) if result.actual_actions else "-"
        failures = ", ".join(result.failure_reasons) if result.failure_reasons else "-"
        run_ref = f" ({rel_path(result.run_path)})" if result.run_path else ""
        lines.append(
            f"| `{result.case_id}` | `{result.split}` | `{result.turn_type}` | {result.status}{run_ref} | {actual} | {failures} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use this report as the next-action classification backbone. It is ready to score captured traces, but it should not be presented as behavior results until run artifacts exist.",
            "",
            "## Failure Analysis",
            "",
            "Failure analysis is deferred until scored traces exist.",
            "",
            "## Next Experiment",
            "",
            "Build or capture isolated `run.json` traces for the current cases, then use this scorer to generate baseline metrics before changing the skill/tool guidance.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT / "evals" / "advisor_tool_use_cases.jsonl",
        help="Path to advisor tool-use case JSONL.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=ROOT / "evals" / "runs" / "next_action",
        help="Directory containing saved run.json artifacts.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "evals" / "reports" / "advisor_tool_use_judgment.md",
        help="Markdown report output path.",
    )
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    run_artifacts = find_run_artifacts(args.runs_dir)
    results = [score_case(case, run_artifacts.get(case["case_id"])) for case in cases]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(cases, results, validation_errors), encoding="utf-8")

    print(
        json.dumps(
            {
                "cases": len(cases),
                "validation_errors": len(validation_errors),
                "run_artifacts": len(run_artifacts),
                "scored_cases": sum(1 for result in results if result.status == "scored"),
                "report": rel_path(args.report),
            },
            indent=2,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
