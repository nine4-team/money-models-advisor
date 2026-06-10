#!/usr/bin/env python3
"""Score source-search query quality seed cases.

This eval only applies after next-action classification has already decided
that `search_source_material` is appropriate for the turn.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import CorpusIndex  # noqa: E402


REQUIRED_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "source_tool_use_case_id",
    "user_turn",
    "retrieval_purpose",
    "expected_layers",
    "focus_terms",
    "query",
    "query_rationale",
    "known_useful_chunk_ids",
    "label_note",
}

PURPOSES = {
    "teaching_evidence",
    "diagnostic_evidence",
    "comparison_evidence",
    "recommendation_evidence",
}

LAYERS = {"unit-economics", "offers", "upsells", "downsells", "continuity"}


@dataclass(frozen=True)
class QueryResult:
    case_id: str
    split: str
    purpose: str
    query: str
    expected_layers: tuple[str, ...]
    returned_ids: tuple[str, ...]
    known_useful_rank: int | None
    useful_at_3: bool
    useful_at_5: bool
    top1_layer_match: bool
    any_layer_match_at_5: bool
    focus_term_recall: float


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for case in cases:
        ref = f"{case.get('case_id', '<missing>')} line {case.get('_line_number', '?')}"
        missing = REQUIRED_FIELDS - set(case)
        if missing:
            errors.append(f"{ref}: missing fields: {', '.join(sorted(missing))}")

        case_id = case.get("case_id")
        if case_id in seen:
            errors.append(f"{ref}: duplicate case_id")
        seen.add(case_id)

        if case.get("retrieval_purpose") not in PURPOSES:
            errors.append(f"{ref}: unknown retrieval_purpose: {case.get('retrieval_purpose')}")

        expected_layers = case.get("expected_layers")
        if not isinstance(expected_layers, list) or not expected_layers:
            errors.append(f"{ref}: expected_layers must be a non-empty list")
        else:
            unknown_layers = sorted(set(expected_layers) - LAYERS)
            if unknown_layers:
                errors.append(f"{ref}: unknown expected_layers: {', '.join(unknown_layers)}")

        for field in ("focus_terms", "known_useful_chunk_ids"):
            if not isinstance(case.get(field), list):
                errors.append(f"{ref}: {field} must be a list")

        if not isinstance(case.get("query"), str) or not case.get("query", "").strip():
            errors.append(f"{ref}: query must be a non-empty string")

    return errors


def focus_term_recall(query: str, focus_terms: list[str]) -> float:
    if not focus_terms:
        return 1.0
    lowered = query.lower()
    hits = sum(1 for term in focus_terms if term.lower() in lowered)
    return hits / len(focus_terms)


def score_cases(cases: list[dict[str, Any]], top_k: int) -> list[QueryResult]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    results: list[QueryResult] = []

    for case in cases:
        expected_layers = tuple(case["expected_layers"])
        layer = expected_layers[0] if len(expected_layers) == 1 else None
        search_results = index.search(case["query"], layer=layer, top_k=top_k)
        returned_ids = tuple(result.chunk.id for result in search_results)
        returned_layers = [set(result.chunk.layers) for result in search_results]
        known_useful = set(case["known_useful_chunk_ids"])

        known_useful_rank = None
        for index_position, chunk_id in enumerate(returned_ids, 1):
            if chunk_id in known_useful:
                known_useful_rank = index_position
                break

        expected_layer_set = set(expected_layers)
        results.append(
            QueryResult(
                case_id=case["case_id"],
                split=case["split"],
                purpose=case["retrieval_purpose"],
                query=case["query"],
                expected_layers=expected_layers,
                returned_ids=returned_ids,
                known_useful_rank=known_useful_rank,
                useful_at_3=known_useful_rank is not None and known_useful_rank <= 3,
                useful_at_5=known_useful_rank is not None and known_useful_rank <= 5,
                top1_layer_match=bool(returned_layers) and bool(returned_layers[0] & expected_layer_set),
                any_layer_match_at_5=any(layers & expected_layer_set for layers in returned_layers[:5]),
                focus_term_recall=focus_term_recall(case["query"], case["focus_terms"]),
            )
        )

    return results


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def render_report(cases: list[dict[str, Any]], results: list[QueryResult], validation_errors: list[str]) -> str:
    lines = [
        "# Advisor Search-Query Quality Eval",
        "",
        "## Scope",
        "",
        "This eval covers only turns where source-material search is the correct next action. It does not evaluate whether the agent should search in the first place; that is covered by the next-action classification eval.",
        "",
        "The known-useful chunk labels are seed relevance labels, not exhaustive relevance judgments. A miss means the query did not retrieve one of the labeled citeable chunks, not that every returned chunk is useless.",
        "",
        "## Dataset",
        "",
        f"- Cases: {len(cases)}",
        f"- Splits: {dict(sorted(Counter(case['split'] for case in cases).items()))}",
        f"- Retrieval purposes: {dict(sorted(Counter(case['retrieval_purpose'] for case in cases).items()))}",
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

    total = len(results)
    avg_focus = sum(result.focus_term_recall for result in results) / total if total else 0.0
    duplicate_queries = {
        query: count for query, count in Counter(result.query.lower() for result in results).items() if count > 1
    }

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Known-useful Hit@3: {pct(sum(result.useful_at_3 for result in results), total)}",
            f"- Known-useful Hit@5: {pct(sum(result.useful_at_5 for result in results), total)}",
            f"- Top-1 layer match: {pct(sum(result.top1_layer_match for result in results), total)}",
            f"- Any expected-layer chunk in top 5: {pct(sum(result.any_layer_match_at_5 for result in results), total)}",
            f"- Average focus-term recall in query text: {avg_focus:.3f}",
            f"- Duplicate query strings: {duplicate_queries or 'none'}",
            "",
            "## Case Table",
            "",
            "| Case | Split | Purpose | Expected Layers | Query | Top Chunks | Known Useful Rank | Focus Recall |",
            "|---|---|---|---|---|---|---:|---:|",
        ]
    )

    for result in results:
        rank = result.known_useful_rank if result.known_useful_rank is not None else "-"
        lines.append(
            "| "
            f"`{result.case_id}` | `{result.split}` | `{result.purpose}` | "
            f"{', '.join(result.expected_layers)} | {result.query} | "
            f"{', '.join(f'`{chunk_id}`' for chunk_id in result.returned_ids) or '-'} | "
            f"{rank} | {result.focus_term_recall:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use this as the first source-search query-quality baseline. Do not compare dense or hybrid retrieval until the query cases and seed labels are reviewed, because retrieval-model differences are hard to interpret when the query formulation itself is unstable.",
            "",
            "## Next Work",
            "",
            "Review broad or low-focus queries, then update `ADVISOR_QUERY_POLICY_V1.md` and the query builder so generated queries are driven by the current source need rather than snapshot status alone.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "advisor_search_query_quality.md")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    results = [] if validation_errors else score_cases(cases, top_k=args.top_k)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(cases, results, validation_errors), encoding="utf-8")

    print(
        json.dumps(
            {
                "cases": len(cases),
                "validation_errors": len(validation_errors),
                "scored_cases": len(results),
                "report": str(args.report.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
