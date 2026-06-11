#!/usr/bin/env python3
"""Score completed source-event traces for multi-search advisor turns.

This eval checks the recorded turn artifact after an acting agent has used the
CLI. It is separate from source-need generation: source-need generation can say
what the agent intended to search, while this eval verifies the completed trace
contains the expected source events.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re


ROOT = Path(__file__).resolve().parents[1]

INTENTS = {
    "teaching_evidence",
    "diagnostic_evidence",
    "comparison_evidence",
    "recommendation_evidence",
}

LAYERS = {"unit-economics", "offers", "upsells", "downsells", "continuity"}

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
class SourceNeed:
    intent: str
    layers: tuple[str, ...]
    focus_terms: tuple[str, ...]


@dataclass(frozen=True)
class EventMatch:
    expected: SourceNeed
    actual: SourceNeed | None
    intent_match: bool
    layer_recall: float
    focus_recall: float
    has_chunks: bool
    query_variant_count: int
    executed_query_variant_count: int


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
    warning_reasons: tuple[str, ...]
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


def validate_source_need(value: Any, case_ref: str, field_name: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{case_ref}: {field_name} must be an object"]

    intent = value.get("intent")
    if intent not in INTENTS:
        errors.append(f"{case_ref}: {field_name}.intent is invalid: {intent}")

    layers = value.get("layers")
    if not isinstance(layers, list) or not layers:
        errors.append(f"{case_ref}: {field_name}.layers must be a non-empty list")
    else:
        unknown_layers = sorted(set(layers) - LAYERS)
        if unknown_layers:
            errors.append(f"{case_ref}: {field_name}.layers unknown values: {', '.join(unknown_layers)}")

    focus_terms = value.get("focus_terms")
    if not isinstance(focus_terms, list) or not focus_terms:
        errors.append(f"{case_ref}: {field_name}.focus_terms must be a non-empty list")
    elif not all(isinstance(term, str) and term.strip() for term in focus_terms):
        errors.append(f"{case_ref}: {field_name}.focus_terms must contain non-empty strings")

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

        expected_events = case.get("expected_source_events")
        if not isinstance(expected_events, list):
            errors.append(f"{case_ref}: expected_source_events must be a list")
        else:
            for index, event in enumerate(expected_events, 1):
                errors.extend(validate_source_need(event, case_ref, f"expected_source_events[{index}]"))

        for field in ("snapshot_fixture_path", "prior_sessions_fixture_path"):
            value = case.get(field)
            if value is None:
                continue
            if not isinstance(value, str):
                errors.append(f"{case_ref}: {field} must be a string or null")
                continue
            if not (ROOT / value).exists():
                errors.append(f"{case_ref}: fixture does not exist: {value}")

    return errors


def parse_source_need(value: Any) -> SourceNeed | None:
    if not isinstance(value, dict):
        return None
    intent = value.get("intent")
    raw_layers = value.get("layers")
    raw_focus_terms = value.get("focus_terms")
    if intent not in INTENTS:
        return None
    if not isinstance(raw_layers, list) or not raw_layers:
        return None
    if not isinstance(raw_focus_terms, list) or not raw_focus_terms:
        return None
    layers = tuple(layer for layer in raw_layers if isinstance(layer, str) and layer in LAYERS)
    focus_terms = tuple(term.strip() for term in raw_focus_terms if isinstance(term, str) and term.strip())
    if not layers or not focus_terms:
        return None
    return SourceNeed(intent=intent, layers=layers, focus_terms=focus_terms)


def expected_needs(case: dict[str, Any]) -> list[SourceNeed]:
    needs = []
    for event in case["expected_source_events"]:
        need = parse_source_need(event)
        if need is None:
            raise ValueError(f"invalid expected_source_events for {case['case_id']}")
        needs.append(need)
    return needs


def actual_events(run: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(run.get("source_events"), list):
        return run["source_events"]
    if isinstance(run.get("turn_record"), dict) and isinstance(run["turn_record"].get("source_events"), list):
        return run["turn_record"]["source_events"]
    return []


def actual_need(event: dict[str, Any]) -> SourceNeed | None:
    return parse_source_need(event.get("source_need"))


def term_recall(expected_terms: tuple[str, ...], actual_terms: tuple[str, ...]) -> float:
    if not expected_terms:
        return 1.0
    actual_text = normalize_text(" ".join(actual_terms))
    hits = sum(1 for term in expected_terms if normalize_text(term) in actual_text)
    return hits / len(expected_terms)


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def layer_recall(expected_layers: tuple[str, ...], actual_layers: tuple[str, ...]) -> float:
    expected = set(expected_layers)
    actual = set(actual_layers)
    return len(expected & actual) / len(expected)


def has_chunks(event: dict[str, Any]) -> bool:
    chunks = event.get("chunks")
    if not isinstance(chunks, list):
        chunks = event.get("inspected_chunks")
    return isinstance(chunks, list) and any(isinstance(chunk, dict) and chunk.get("id") for chunk in chunks)


def query_variant_count(event: dict[str, Any]) -> int:
    return len(query_variants(event))


def query_variants(event: dict[str, Any]) -> list[str]:
    source_need = event.get("source_need")
    if not isinstance(source_need, dict):
        return []
    variants = source_need.get("query_variants")
    if not isinstance(variants, list):
        return []
    return [variant.strip() for variant in variants if isinstance(variant, str) and variant.strip()]


def executed_query_variant_count(event: dict[str, Any]) -> int:
    queries = event.get("queries")
    if queries is None and isinstance(event.get("query"), str):
        queries = [event["query"]]
    if not isinstance(queries, list):
        return 0
    executed = {normalize_query_text(query) for query in queries if isinstance(query, str)}
    return sum(1 for variant in query_variants(event) if normalize_query_text(variant) in executed)


def normalize_query_text(value: str) -> str:
    return " ".join(value.split()).lower()


def find_best_match(expected: SourceNeed, events: list[dict[str, Any]], used_indexes: set[int]) -> tuple[int | None, EventMatch]:
    best_index = None
    best_match = EventMatch(expected, None, False, 0.0, 0.0, False, 0, 0)
    best_score = -1.0
    for index, event in enumerate(events):
        if index in used_indexes:
            continue
        need = actual_need(event)
        if need is None:
            continue
        intent_match = need.intent == expected.intent
        layers = layer_recall(expected.layers, need.layers)
        focus = term_recall(expected.focus_terms, need.focus_terms)
        chunks = has_chunks(event)
        variants = query_variant_count(event)
        executed_variants = executed_query_variant_count(event)
        score = (2.0 if intent_match else 0.0) + layers + focus + (0.25 if chunks else 0.0)
        if score > best_score:
            best_index = index
            best_score = score
            best_match = EventMatch(expected, need, intent_match, layers, focus, chunks, variants, executed_variants)
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


def score_case(case: dict[str, Any], run_path: Path | None, *, require_query_variants: bool = False) -> CaseResult:
    expected = expected_needs(case)
    if run_path is None:
        return CaseResult(
            case_id=case["case_id"],
            split=case["split"],
            expected_event_count=len(expected),
            actual_event_count=None,
            matched_event_count=0,
            all_expected_events_matched=None,
            extra_event_count=None,
            status="not_run",
            failure_reasons=(),
            warning_reasons=(),
            event_matches=(),
        )

    run = json.loads(run_path.read_text(encoding="utf-8"))
    events = actual_events(run)
    if not expected:
        failures = [f"unexpected_source_events:{len(events)}"] if events else []
        return CaseResult(
            case_id=case["case_id"],
            split=case["split"],
            expected_event_count=0,
            actual_event_count=len(events),
            matched_event_count=0,
            all_expected_events_matched=not failures,
            extra_event_count=len(events),
            status="failed" if failures else "passed",
            failure_reasons=tuple(failures),
            warning_reasons=(),
            event_matches=(),
        )

    used_indexes: set[int] = set()
    matches: list[EventMatch] = []
    failures: list[str] = []
    for need in expected:
        index, match = find_best_match(need, events, used_indexes)
        if index is not None:
            used_indexes.add(index)
        matches.append(match)
        if not match.intent_match:
            failures.append(f"missing_intent:{need.intent}")
        if match.layer_recall < 1.0:
            failures.append(f"layer_miss:{need.intent}")
        if match.focus_recall < 0.5:
            failures.append(f"focus_miss:{need.intent}")
        if not match.has_chunks:
            failures.append(f"missing_chunks:{need.intent}")
        if require_query_variants and not 2 <= match.query_variant_count <= 4:
            failures.append(f"missing_query_variants:{need.intent}")
        if require_query_variants and match.executed_query_variant_count != match.query_variant_count:
            failures.append(f"unexecuted_query_variants:{need.intent}")

    extra_events = max(0, len(events) - len(used_indexes))
    matched = sum(
        match.intent_match
        and match.layer_recall >= 1.0
        and match.focus_recall >= 0.5
        and match.has_chunks
        and (
            not require_query_variants
            or (2 <= match.query_variant_count <= 4 and match.executed_query_variant_count == match.query_variant_count)
        )
        for match in matches
    )
    all_matched = matched == len(expected)
    if extra_events:
        warnings = [f"extra_events:{extra_events}"]
    else:
        warnings = []
    status = "passed" if all_matched else "failed"
    return CaseResult(
        case_id=case["case_id"],
        split=case["split"],
        expected_event_count=len(expected),
        actual_event_count=len(events),
        matched_event_count=matched,
        all_expected_events_matched=all_matched,
        extra_event_count=extra_events,
        status=status,
        failure_reasons=tuple(failures),
        warning_reasons=tuple(warnings),
        event_matches=tuple(matches),
    )


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def render_report(
    cases: list[dict[str, Any]],
    results: list[CaseResult],
    validation_errors: list[str],
    *,
    require_query_variants: bool = False,
) -> str:
    scored = [result for result in results if result.status != "not_run"]
    passed = [result for result in scored if result.status == "passed"]
    lines = [
        "# Advisor Source-Event Trace Eval",
        "",
        "## Scope",
        "",
        "This eval checks completed advisor-turn traces. It verifies that source-backed answers contain the expected source events, multi-job answers split retrieval into distinct SourceNeeds, and no-search turns do not fabricate source events.",
        "",
        "It does not run an agent and does not call external model services. Acting agents complete traces separately; this scorer validates the resulting `run.json` artifacts.",
        "",
        "## Trace Requirement",
        "",
        "- Query variants required: " + ("yes" if require_query_variants else "no"),
        "- Query variants must be present in executed queries: " + ("yes" if require_query_variants else "no"),
        "",
        "## Dataset",
        "",
        f"- Cases: {len(cases)}",
        f"- Splits: {dict(sorted(Counter(case['split'] for case in cases).items()))}",
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

    lines.extend(
        [
            "",
            "## Run Coverage",
            "",
            f"- Scored runs: {len(scored)} / {len(cases)}",
            f"- Missing runs: {len(cases) - len(scored)}",
            "",
            "## Metrics",
            "",
        ]
    )
    if scored:
        lines.extend(
            [
                f"- Case pass rate: {pct(len(passed), len(scored))}",
                f"- Expected source events matched: {sum(result.matched_event_count for result in scored)} / {sum(result.expected_event_count for result in scored)}",
                f"- Extra source-event warnings: {sum(1 for result in scored if result.extra_event_count)} cases / {sum(result.extra_event_count or 0 for result in scored)} events",
            ]
        )
    else:
        lines.append("- Status: inventory only; no source-event run artifacts found yet.")

    lines.extend(
        [
            "",
            "## Case Table",
            "",
            "| Case | Split | Expected Events | Actual Events | Matched Events | Status | Findings |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for result in results:
        lines.append(
            "| "
            f"`{result.case_id}` | `{result.split}` | {result.expected_event_count} | "
            f"{'-' if result.actual_event_count is None else result.actual_event_count} | "
            f"{result.matched_event_count} | `{result.status}` | "
            f"{', '.join([*result.failure_reasons, *result.warning_reasons]) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use this eval to validate post-hardening acting-agent traces before claiming that the advisor reliably decides when to search, when not to search, and when to split one answer into multiple source-material searches.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_source_event_cases.jsonl")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=ROOT / "evals" / "runs" / "source_events" / "post_hardening_expanded_v2",
    )
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "advisor_source_event_traces.md")
    parser.add_argument(
        "--require-query-variants",
        action="store_true",
        help="Fail matched source events unless source_need.query_variants contains at least two agent-written variants.",
    )
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    artifacts = find_run_artifacts(args.runs_dir)
    results = [] if validation_errors else [
        score_case(case, artifacts.get(case["case_id"]), require_query_variants=args.require_query_variants) for case in cases
    ]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(cases, results, validation_errors, require_query_variants=args.require_query_variants),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "cases": len(cases),
                "validation_errors": len(validation_errors),
                "scored_runs": sum(result.status != "not_run" for result in results),
                "report": rel_path(args.report),
            },
            indent=2,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
