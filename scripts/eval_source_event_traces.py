#!/usr/bin/env python3
"""Score completed source-event traces against the active SearchRequest contract."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INTENTS = {
    "teaching_evidence",
    "diagnostic_evidence",
    "comparison_evidence",
    "recommendation_evidence",
}
REQUIRED_CASE_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "conversation_context",
    "snapshot_fixture_path",
    "prior_sessions_fixture_path",
    "user_turn",
    "expected_source_events",
    "label_rationale",
    "ambiguity",
    "severity_if_wrong",
}


@dataclass(frozen=True)
class ExpectedEvent:
    job: str
    required_query_concepts: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class EventMatch:
    expected: ExpectedEvent
    query: str | None
    concept_recall: float
    current_contract: bool
    user_turn_match: bool
    query_executed: bool
    has_chunks: bool


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    split: str
    expected_event_count: int
    actual_event_count: int | None
    matched_event_count: int
    all_expected_events_matched: bool | None
    extra_event_count: int | None
    status: str
    failure_reasons: tuple[str, ...]
    event_matches: tuple[EventMatch, ...]


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


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def validate_expected_event(value: Any, case_ref: str, field_name: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{case_ref}: {field_name} must be an object"]
    errors: list[str] = []
    if not isinstance(value.get("job"), str) or not value["job"].strip():
        errors.append(f"{case_ref}: {field_name}.job must be a non-empty string")
    concepts = value.get("required_query_concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append(f"{case_ref}: {field_name}.required_query_concepts must be a non-empty list")
    else:
        for index, alternatives in enumerate(concepts, 1):
            if (
                not isinstance(alternatives, list)
                or not alternatives
                or not all(isinstance(term, str) and term.strip() for term in alternatives)
            ):
                errors.append(
                    f"{case_ref}: {field_name}.required_query_concepts[{index}] must contain non-empty alternatives"
                )
    return errors


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
        expected = case.get("expected_source_events")
        if not isinstance(expected, list):
            errors.append(f"{case_ref}: expected_source_events must be a list")
        else:
            for index, event in enumerate(expected, 1):
                errors.extend(validate_expected_event(event, case_ref, f"expected_source_events[{index}]"))
        for field in ("snapshot_fixture_path", "prior_sessions_fixture_path"):
            value = case.get(field)
            if value is not None and (not isinstance(value, str) or not (ROOT / value).exists()):
                errors.append(f"{case_ref}: invalid fixture: {field}={value}")
    return errors


def expected_events(case: dict[str, Any]) -> list[ExpectedEvent]:
    return [
        ExpectedEvent(
            job=event["job"],
            required_query_concepts=tuple(tuple(group) for group in event["required_query_concepts"]),
        )
        for event in case["expected_source_events"]
    ]


def actual_events(run: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(run.get("source_events"), list):
        return run["source_events"]
    record = run.get("turn_record")
    if isinstance(record, dict) and isinstance(record.get("source_events"), list):
        return record["source_events"]
    return []


def event_match(expected: ExpectedEvent, event: dict[str, Any], user_turn: str) -> EventMatch:
    request = event.get("search_request")
    current_contract = isinstance(request, dict) and request.get("intent") in INTENTS
    query = request.get("query") if isinstance(request, dict) else None
    if not isinstance(query, str) or not query.strip():
        query = None
        current_contract = False
    request_turn = request.get("user_turn") if isinstance(request, dict) else None
    user_turn_match = isinstance(request_turn, str) and normalize_text(request_turn) == normalize_text(user_turn)
    query_text = normalize_text(query or "")
    hits = sum(
        any(normalize_text(alternative) in query_text for alternative in alternatives)
        for alternatives in expected.required_query_concepts
    )
    concept_recall = hits / len(expected.required_query_concepts)
    queries = event.get("queries")
    if queries is None and isinstance(event.get("query"), str):
        queries = [event["query"]]
    query_executed = (
        query is not None
        and isinstance(queries, list)
        and len(queries) == 1
        and isinstance(queries[0], str)
        and normalize_text(queries[0]) == normalize_text(query)
    )
    chunks = event.get("chunks")
    has_chunks = isinstance(chunks, list) and any(isinstance(chunk, dict) and chunk.get("id") for chunk in chunks)
    return EventMatch(expected, query, concept_recall, current_contract, user_turn_match, query_executed, has_chunks)


def match_passes(match: EventMatch) -> bool:
    return (
        match.concept_recall == 1.0
        and match.current_contract
        and match.user_turn_match
        and match.query_executed
        and match.has_chunks
    )


def find_best_match(
    expected: ExpectedEvent,
    events: list[dict[str, Any]],
    used_indexes: set[int],
    user_turn: str,
) -> tuple[int | None, EventMatch]:
    empty = EventMatch(expected, None, 0.0, False, False, False, False)
    best_index: int | None = None
    best_match = empty
    best_score = -1.0
    for index, event in enumerate(events):
        if index in used_indexes:
            continue
        match = event_match(expected, event, user_turn)
        score = (
            match.concept_recall * 4
            + int(match.current_contract)
            + int(match.user_turn_match)
            + int(match.query_executed)
            + int(match.has_chunks)
        )
        if score > best_score:
            best_index, best_match, best_score = index, match, score
    return best_index, best_match


def find_run_artifacts(runs_dir: Path) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    if not runs_dir.exists():
        return artifacts
    for path in sorted(runs_dir.rglob("run.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        case_id = payload.get("case_id")
        if isinstance(case_id, str):
            artifacts[case_id] = path
    return artifacts


def score_case(case: dict[str, Any], run_path: Path | None) -> CaseResult:
    expected = expected_events(case)
    if run_path is None:
        return CaseResult(case["case_id"], case["split"], len(expected), None, 0, None, None, "not_run", (), ())
    run = json.loads(run_path.read_text(encoding="utf-8"))
    events = actual_events(run)
    if not expected:
        failures = (f"unexpected_source_events:{len(events)}",) if events else ()
        return CaseResult(
            case["case_id"], case["split"], 0, len(events), 0, not failures, len(events),
            "failed" if failures else "passed", failures, (),
        )

    used: set[int] = set()
    matches: list[EventMatch] = []
    failures: list[str] = []
    for expected_event in expected:
        index, match = find_best_match(expected_event, events, used, case["user_turn"])
        if index is not None:
            used.add(index)
        matches.append(match)
        if not match.current_contract:
            failures.append(f"current_contract_missing:{expected_event.job}")
        if not match.user_turn_match:
            failures.append(f"user_turn_mismatch:{expected_event.job}")
        if match.concept_recall < 1.0:
            failures.append(f"query_concept_miss:{expected_event.job}:{match.concept_recall:.3f}")
        if not match.query_executed:
            failures.append(f"query_not_executed:{expected_event.job}")
        if not match.has_chunks:
            failures.append(f"missing_chunks:{expected_event.job}")
    extra = max(0, len(events) - len(used))
    if extra:
        failures.append(f"extra_events:{extra}")
    matched = sum(match_passes(match) for match in matches)
    passed = matched == len(expected) and extra == 0
    return CaseResult(
        case["case_id"], case["split"], len(expected), len(events), matched, passed, extra,
        "passed" if passed else "failed", tuple(failures), tuple(matches),
    )


def pct(count: int, total: int) -> str:
    return "n/a" if total == 0 else f"{count / total * 100:.1f}%"


def render_report(cases: list[dict[str, Any]], results: list[CaseResult], validation_errors: list[str]) -> str:
    scored = [result for result in results if result.status != "not_run"]
    passed = [result for result in scored if result.status == "passed"]
    lines = [
        "# Advisor Source-Event Trace Eval",
        "",
        "## Scope",
        "",
        "This scorer checks completed turns against the active single-query `SearchRequest` contract. It verifies search/no-search restraint, one event per evidence job, required query concepts, exact query execution, and inspected chunk recording.",
        "",
        "`intent` must be a valid trace label but is not compared with an answer key because it does not control retrieval.",
        "",
        "## Dataset",
        "",
        f"- Cases: {len(cases)}",
        f"- Splits: {dict(sorted(Counter(case['split'] for case in cases).items()))}",
        "",
        "## Validation",
        "",
        "- Status: passed" if not validation_errors else f"- Status: failed ({len(validation_errors)} issues)",
    ]
    lines.extend(f"- {error}" for error in validation_errors)
    lines.extend([
        "", "## Run Coverage", "",
        f"- Scored runs: {len(scored)} / {len(cases)}",
        f"- Missing runs: {len(cases) - len(scored)}",
        "", "## Metrics", "",
    ])
    if scored:
        lines.extend([
            f"- Case pass rate: {pct(len(passed), len(scored))}",
            f"- Expected source events matched: {sum(r.matched_event_count for r in scored)} / {sum(r.expected_event_count for r in scored)}",
            f"- Extra source events: {sum(r.extra_event_count or 0 for r in scored)}",
        ])
    else:
        lines.append("- No current-contract run artifacts found.")
    lines.extend([
        "", "## Case Table", "",
        "| Case | Expected | Actual | Matched | Status | Findings |",
        "|---|---:|---:|---:|---|---|",
    ])
    for result in results:
        lines.append(
            f"| `{result.case_id}` | {result.expected_event_count} | "
            f"{'-' if result.actual_event_count is None else result.actual_event_count} | "
            f"{result.matched_event_count} | `{result.status}` | {', '.join(result.failure_reasons) or '-'} |"
        )
    audited_cases = [case for case in cases if isinstance(case.get("label_audit"), dict)]
    if audited_cases:
        lines.extend([
            "",
            "## Answer-Key Audit",
            "",
            "The run artifacts were frozen before these label corrections; queries and retrieval were not rerun.",
            "",
        ])
        for case in audited_cases:
            audit = case["label_audit"]
            lines.append(
                f"- `{case['case_id']}`: {audit.get('correction', 'label corrected')}. "
                f"{audit.get('reason', '')}".rstrip()
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_source_event_cases.jsonl")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "source_events" / "search_request_v1")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "advisor_source_event_traces.md")
    args = parser.parse_args()
    cases = load_jsonl(args.cases)
    errors = validate_cases(cases)
    artifacts = find_run_artifacts(args.runs_dir)
    results = [] if errors else [score_case(case, artifacts.get(case["case_id"])) for case in cases]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(cases, results, errors), encoding="utf-8")
    print(json.dumps({
        "cases": len(cases),
        "validation_errors": len(errors),
        "scored_runs": sum(result.status != "not_run" for result in results),
        "passed_runs": sum(result.status == "passed" for result in results),
        "report": rel_path(args.report),
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
