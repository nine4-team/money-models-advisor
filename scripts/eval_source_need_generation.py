#!/usr/bin/env python3
"""Score source-need generation traces for the Money Model Advisor.

This eval sits between next-action classification and query generation. It does
not run an agent. It validates labeled cases and scores saved run artifacts when
they exist under `evals/runs/source_need/**/run.json`.
"""

from __future__ import annotations

import argparse
import json
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

LAYERS = {"unit-economics", "offers", "upsells", "downsells", "continuity"}

REQUIRED_CASE_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "conversation_context",
    "snapshot_fixture_path",
    "prior_sessions_fixture_path",
    "user_turn",
    "expected_search",
    "expected_source_need",
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
class CaseResult:
    case_id: str
    split: str
    expected_search: bool
    actual_search: bool | None
    status: str
    intent_match: bool | None
    layer_exact_match: bool | None
    layer_recall: float | None
    focus_recall: float | None
    false_search: bool | None
    missed_search: bool | None
    actual_source_need: SourceNeed | None
    failure_reasons: tuple[str, ...]


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
        return [f"{case_ref}: {field_name} must be an object or null"]

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

        expected_search = case.get("expected_search")
        if not isinstance(expected_search, bool):
            errors.append(f"{case_ref}: expected_search must be boolean")

        source_need = case.get("expected_source_need")
        if expected_search is True:
            errors.extend(validate_source_need(source_need, case_ref, "expected_source_need"))
            acceptable_intents = case.get("acceptable_intents")
            if acceptable_intents is not None:
                if not isinstance(acceptable_intents, list) or not acceptable_intents:
                    errors.append(f"{case_ref}: acceptable_intents must be a non-empty list when present")
                else:
                    unknown_intents = sorted(set(acceptable_intents) - INTENTS)
                    if unknown_intents:
                        errors.append(f"{case_ref}: acceptable_intents unknown values: {', '.join(unknown_intents)}")
                    expected_intent = source_need.get("intent") if isinstance(source_need, dict) else None
                    if expected_intent in INTENTS and expected_intent not in acceptable_intents:
                        errors.append(f"{case_ref}: acceptable_intents must include expected_source_need.intent")
        elif source_need is not None:
            errors.append(f"{case_ref}: expected_source_need must be null when expected_search is false")
        elif case.get("acceptable_intents") is not None:
            errors.append(f"{case_ref}: acceptable_intents must be omitted when expected_search is false")

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


def parse_source_need(value: Any) -> tuple[SourceNeed | None, list[str]]:
    if value is None:
        return None, []
    if not isinstance(value, dict):
        return None, ["source_need_not_object"]

    intent = value.get("intent")
    raw_layers = value.get("layers", [])
    raw_focus_terms = value.get("focus_terms", [])
    failures: list[str] = []

    if intent not in INTENTS:
        failures.append(f"invalid_intent:{intent}")
    if not isinstance(raw_layers, list):
        failures.append("layers_not_list")
        raw_layers = []
    if not isinstance(raw_focus_terms, list):
        failures.append("focus_terms_not_list")
        raw_focus_terms = []

    layers = tuple(str(layer) for layer in raw_layers if isinstance(layer, str) and layer in LAYERS)
    focus_terms = tuple(term.strip() for term in raw_focus_terms if isinstance(term, str) and term.strip())

    if not layers:
        failures.append("missing_valid_layers")
    if not focus_terms:
        failures.append("missing_focus_terms")
    if failures:
        return None, failures
    return SourceNeed(intent=str(intent), layers=layers, focus_terms=focus_terms), []


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


def extract_actual(run: dict[str, Any]) -> tuple[bool | None, SourceNeed | None, list[str]]:
    failures: list[str] = []
    raw_need = run.get("source_need", run.get("actual_source_need"))
    raw_decision = run.get("source_search_decision")

    source_need, parse_failures = parse_source_need(raw_need)
    failures.extend(parse_failures)

    if isinstance(raw_decision, bool):
        actual_search = raw_decision
    elif raw_need is None:
        actual_search = False
    elif source_need is not None:
        actual_search = True
    else:
        actual_search = None
        failures.append("missing_source_search_decision")

    if actual_search is True and source_need is None:
        failures.append("search_true_but_no_valid_source_need")
    if actual_search is False and source_need is not None:
        failures.append("source_need_present_when_search_false")

    return actual_search, source_need, failures


def expected_need(case: dict[str, Any]) -> SourceNeed | None:
    source_need = case.get("expected_source_need")
    if source_need is None:
        return None
    parsed, failures = parse_source_need(source_need)
    if failures:
        raise ValueError(f"invalid expected_source_need for {case['case_id']}: {failures}")
    return parsed


def acceptable_intents(case: dict[str, Any], expected: SourceNeed | None) -> set[str]:
    raw_intents = case.get("acceptable_intents")
    if isinstance(raw_intents, list):
        return {intent for intent in raw_intents if isinstance(intent, str)}
    if expected is None:
        return set()
    return {expected.intent}


def term_recall(expected_terms: tuple[str, ...], actual_terms: tuple[str, ...]) -> float:
    if not expected_terms:
        return 1.0
    actual_text = " ".join(actual_terms).lower()
    hits = sum(1 for term in expected_terms if term.lower() in actual_text)
    return hits / len(expected_terms)


def score_case(case: dict[str, Any], run_path: Path | None) -> CaseResult:
    if run_path is None:
        return CaseResult(
            case_id=case["case_id"],
            split=case["split"],
            expected_search=case["expected_search"],
            actual_search=None,
            status="not_run",
            intent_match=None,
            layer_exact_match=None,
            layer_recall=None,
            focus_recall=None,
            false_search=None,
            missed_search=None,
            actual_source_need=None,
            failure_reasons=(),
        )

    run = json.loads(run_path.read_text(encoding="utf-8"))
    actual_search, actual_need, failures = extract_actual(run)
    expected_search = case["expected_search"]
    expected = expected_need(case)

    false_search = actual_search is True and expected_search is False
    missed_search = actual_search is False and expected_search is True

    intent_match = None
    layer_exact_match = None
    layer_recall = None
    focus_recall = None

    if expected_search and actual_need is not None and expected is not None:
        intent_match = actual_need.intent in acceptable_intents(case, expected)
        expected_layers = set(expected.layers)
        actual_layers = set(actual_need.layers)
        layer_exact_match = actual_layers == expected_layers
        layer_recall = len(expected_layers & actual_layers) / len(expected_layers)
        focus_recall = term_recall(expected.focus_terms, actual_need.focus_terms)
    elif not expected_search:
        intent_match = actual_need is None
        layer_exact_match = actual_need is None
        layer_recall = 1.0 if actual_need is None else 0.0
        focus_recall = 1.0 if actual_need is None else 0.0

    if actual_search is None:
        failures.append("actual_search_unknown")

    status = "scored" if not failures else "scored_with_trace_issues"
    return CaseResult(
        case_id=case["case_id"],
        split=case["split"],
        expected_search=expected_search,
        actual_search=actual_search,
        status=status,
        intent_match=intent_match,
        layer_exact_match=layer_exact_match,
        layer_recall=layer_recall,
        focus_recall=focus_recall,
        false_search=false_search,
        missed_search=missed_search,
        actual_source_need=actual_need,
        failure_reasons=tuple(failures),
    )


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def avg(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return sum(real_values) / len(real_values)


def fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def render_report(cases: list[dict[str, Any]], results: list[CaseResult], validation_errors: list[str]) -> str:
    scored = [result for result in results if result.status != "not_run"]
    search_expected = [result for result in scored if result.expected_search]
    no_search_expected = [result for result in scored if not result.expected_search]
    lines = [
        "# Advisor Source-Need Generation Eval",
        "",
        "## Scope",
        "",
        "This eval checks the step between next-action classification and query construction. Given conversation context, snapshot state, and the current user turn, the acting agent should decide whether source-material search is needed and, if it is, generate a structured source need.",
        "",
        "A source need contains retrieval intent, corpus layer or layers, and focus terms. The query builder then turns that structure into a concrete search query.",
        "",
        "Some labeled cases may include `acceptable_intents`. That is eval-only label tolerance for turns where more than one primary retrieval objective is defensible; runtime source needs still emit one intent per source-material search call.",
        "",
        "This script does not run an agent and does not call external model services. It validates labels and scores saved `run.json` artifacts when they exist under `evals/runs/source_need/`.",
        "",
        "## Dataset",
        "",
        f"- Cases: {len(cases)}",
        f"- Splits: {dict(sorted(Counter(case['split'] for case in cases).items()))}",
        f"- Expected search: {dict(sorted(Counter(case['expected_search'] for case in cases).items()))}",
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

    if not scored:
        lines.append("- Status: inventory only; no source-need run artifacts found yet.")
    else:
        search_decision_accuracy = sum(result.actual_search == result.expected_search for result in scored)
        false_search_count = sum(bool(result.false_search) for result in scored)
        missed_search_count = sum(bool(result.missed_search) for result in scored)
        intent_matches = sum(result.intent_match is True for result in search_expected)
        layer_exact_matches = sum(result.layer_exact_match is True for result in search_expected)
        average_layer_recall = avg([result.layer_recall for result in search_expected])
        average_focus_recall = avg([result.focus_recall for result in search_expected])
        correct_no_search = sum(result.actual_search is False for result in no_search_expected)
        lines.extend(
            [
                f"- Search decision accuracy: {pct(search_decision_accuracy, len(scored))}",
                f"- False search rate: {pct(false_search_count, len(scored))}",
                f"- Missed search rate: {pct(missed_search_count, len(scored))}",
                f"- Intent match on expected-search cases: {pct(intent_matches, len(search_expected))}",
                f"- Layer exact match on expected-search cases: {pct(layer_exact_matches, len(search_expected))}",
                f"- Average layer recall on expected-search cases: {fmt(average_layer_recall)}",
                f"- Average focus-term recall on expected-search cases: {fmt(average_focus_recall)}",
                f"- Correct no-search controls: {pct(correct_no_search, len(no_search_expected))}",
            ]
        )

        lines.extend(
            [
                "",
                "## Interpretation",
                "",
            ]
        )
        if false_search_count == 0 and missed_search_count == 0:
            lines.append("- The search/no-search boundary is clean on this seed set.")
        else:
            lines.append("- The search/no-search boundary still needs instruction or tool-surface work before retrieval-backend comparisons.")
        if intent_matches < len(search_expected) or layer_exact_matches < len(search_expected):
            lines.append("- Source-need precision is still partial; inspect intent and layer misses before treating retrieval-backend comparisons as meaningful.")
        if average_focus_recall is not None and average_focus_recall < 0.7:
            lines.append("- Focus-term recall is low enough that the metric should be treated as a development signal, not a production-quality semantic score.")

    lines.extend(
        [
            "",
            "## Case Table",
            "",
            "| Case | Split | Expected Search | Actual Search | Intent Match | Layer Recall | Focus Recall | Status | Failure Reasons |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for result in results:
        lines.append(
            "| "
            f"`{result.case_id}` | `{result.split}` | {str(result.expected_search).lower()} | "
            f"{'-' if result.actual_search is None else str(result.actual_search).lower()} | "
            f"{'-' if result.intent_match is None else str(result.intent_match).lower()} | "
            f"{fmt(result.layer_recall)} | {fmt(result.focus_recall)} | "
            f"`{result.status}` | "
            f"{', '.join(result.failure_reasons) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use this eval before comparing BM25, dense, or hybrid retrieval. If the acting agent chooses the wrong source need, retrieval-backend comparisons will mostly measure upstream planning noise.",
            "",
            "## Expected Run Artifact Shape",
            "",
            "```json",
            json.dumps(
                {
                    "case_id": "sourceneed_v1_001",
                    "source_search_decision": True,
                    "source_need": {
                        "intent": "teaching_evidence",
                        "layers": ["unit-economics"],
                        "focus_terms": ["gross profit", "fulfillment cost", "CAC", "payback period"],
                    },
                },
                indent=2,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_source_need_cases.jsonl")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "source_need")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "advisor_source_need_generation.md")
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    artifacts = find_run_artifacts(args.runs_dir)
    results = [] if validation_errors else [score_case(case, artifacts.get(case["case_id"])) for case in cases]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(cases, results, validation_errors), encoding="utf-8")
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
