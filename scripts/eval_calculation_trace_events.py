#!/usr/bin/env python3
"""Score calculation-trace acting-agent runs.

This eval checks whether an agent-operated CLI turn recorded auditable
calculation events when the workflow used deterministic math.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CASE_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "conversation_context",
    "snapshot_fixture_path",
    "prior_sessions_fixture_path",
    "user_turn",
    "expected_calculation_events",
    "expected_actions",
    "forbidden_actions",
    "label_rationale",
    "ambiguity",
    "severity_if_wrong",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            record["_line_number"] = line_number
            records.append(record)
    return records


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
        for field in ("snapshot_fixture_path", "prior_sessions_fixture_path"):
            value = case.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not (ROOT / value).exists():
                errors.append(f"{case_ref}: fixture does not exist: {value}")
        expected_events = case.get("expected_calculation_events")
        if not isinstance(expected_events, list):
            errors.append(f"{case_ref}: expected_calculation_events must be a list")
            continue
        for index, event in enumerate(expected_events, 1):
            errors.extend(validate_calculation_event(event, f"{case_ref}: expected_calculation_events[{index}]"))
    return errors


def validate_calculation_event(event: Any, label: str) -> list[str]:
    if not isinstance(event, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    if not isinstance(event.get("metric"), str) or not event["metric"].strip():
        errors.append(f"{label}.metric must be a non-empty string")
    if not isinstance(event.get("inputs"), dict) or not event["inputs"]:
        errors.append(f"{label}.inputs must be a non-empty object")
    if not isinstance(event.get("value"), (int, float)):
        errors.append(f"{label}.value must be a number")
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


def actual_actions(run: dict[str, Any]) -> list[str]:
    raw = run.get("actual_actions", run.get("actions", []))
    actions: list[str] = []
    if not isinstance(raw, list):
        return actions
    for item in raw:
        if isinstance(item, str):
            actions.append(item)
        elif isinstance(item, dict):
            action = item.get("action") or item.get("type")
            if isinstance(action, str):
                actions.append(action)
    return actions


def calculation_events(run: dict[str, Any]) -> list[dict[str, Any]]:
    events = run.get("calculation_events")
    if isinstance(events, list):
        return [event for event in events if isinstance(event, dict)]
    turn_record = run.get("turn_record")
    if isinstance(turn_record, dict) and isinstance(turn_record.get("calculation_events"), list):
        return [event for event in turn_record["calculation_events"] if isinstance(event, dict)]
    return []


def event_matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    if expected.get("metric") != actual.get("metric"):
        return False
    if expected.get("inputs") != actual.get("inputs"):
        return False
    expected_value = expected.get("value")
    actual_value = actual.get("value")
    if not isinstance(expected_value, (int, float)) or not isinstance(actual_value, (int, float)):
        return False
    return math.isclose(float(expected_value), float(actual_value), rel_tol=1e-6, abs_tol=1e-9)


def score_case(case: dict[str, Any], run_path: Path | None) -> dict[str, Any]:
    if run_path is None:
        return {
            "case_id": case["case_id"],
            "status": "missing_run",
            "failure_reasons": ["missing_run"],
            "actual_actions": [],
            "actual_calculation_events": [],
            "run_path": None,
        }
    run = json.loads(run_path.read_text(encoding="utf-8"))
    actions = actual_actions(run)
    events = calculation_events(run)
    failures: list[str] = []

    for action in case["expected_actions"]:
        if action not in actions:
            failures.append(f"missing_action:{action}")
    for action in case["forbidden_actions"]:
        if action in actions:
            failures.append(f"forbidden_action:{action}")

    unmatched = events.copy()
    for expected in case["expected_calculation_events"]:
        match_index = next((index for index, actual in enumerate(unmatched) if event_matches(expected, actual)), None)
        if match_index is None:
            failures.append(f"missing_calculation_event:{expected.get('metric')}")
        else:
            unmatched.pop(match_index)

    if not case["expected_calculation_events"] and events:
        failures.append("unexpected_calculation_event")
    if "calculate" in actions and not events:
        failures.append("calculate_without_calculation_events")

    return {
        "case_id": case["case_id"],
        "status": "pass" if not failures else "fail",
        "failure_reasons": failures,
        "actual_actions": actions,
        "actual_calculation_events": events,
        "run_path": rel_path(run_path),
    }


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score calculation trace acting-agent runs")
    parser.add_argument("--cases", default="evals/advisor_calculation_trace_cases.jsonl")
    parser.add_argument("--runs-dir", default="evals/runs/calculation_trace")
    args = parser.parse_args()

    cases = load_jsonl(ROOT / args.cases)
    errors = validate_cases(cases)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        return 1

    runs = find_run_artifacts(ROOT / args.runs_dir)
    results = [score_case(case, runs.get(case["case_id"])) for case in cases]
    status_counts = Counter(result["status"] for result in results)
    failure_counts = Counter(reason for result in results for reason in result["failure_reasons"])
    print(
        json.dumps(
            {
                "valid": True,
                "cases": len(cases),
                "runs": len(runs),
                "status_counts": dict(status_counts),
                "failure_counts": dict(failure_counts),
                "results": results,
            },
            indent=2,
        )
    )
    return 0 if not failure_counts and status_counts.get("missing_run", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
