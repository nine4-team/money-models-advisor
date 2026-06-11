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

from money_model_architect.advisor_queries import SourceNeed, build_advisor_queries  # noqa: E402
from money_model_architect.retrieval import CorpusIndex  # noqa: E402
from money_model_architect.snapshot import BusinessSnapshot  # noqa: E402


REQUIRED_FIELDS = {
    "case_id",
    "split",
    "scenario_id",
    "source_tool_use_case_id",
    "user_turn",
    "retrieval_purpose",
    "expected_layers",
    "focus_terms",
    "reference_query",
    "query_rationale",
    "known_useful_chunk_ids",
    "label_note",
    "snapshot_fixture_path",
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
    query_source: str
    retrieval_backend: str
    queries: tuple[str, ...]
    query_layers: tuple[str | None, ...]
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

        if not isinstance(case.get("reference_query"), str) or not case.get("reference_query", "").strip():
            errors.append(f"{ref}: reference_query must be a non-empty string")

        snapshot_fixture = case.get("snapshot_fixture_path")
        if not isinstance(snapshot_fixture, str) or not snapshot_fixture.strip():
            errors.append(f"{ref}: snapshot_fixture_path must be a non-empty string")
        elif not (ROOT / snapshot_fixture).exists():
            errors.append(f"{ref}: snapshot fixture does not exist: {snapshot_fixture}")

    return errors


def focus_term_recall(query: str, focus_terms: list[str]) -> float:
    if not focus_terms:
        return 1.0
    lowered = query.lower()
    hits = sum(1 for term in focus_terms if term.lower() in lowered)
    return hits / len(focus_terms)


def query_specs_for_case(case: dict[str, Any], query_source: str) -> list[tuple[str | None, str]]:
    if query_source == "reference":
        expected_layers = case["expected_layers"]
        layer = expected_layers[0] if len(expected_layers) == 1 else None
        return [(layer, case["reference_query"])]

    snapshot = BusinessSnapshot.load(ROOT / case["snapshot_fixture_path"])
    source_need = SourceNeed(
        intent=case["retrieval_purpose"],
        layers=tuple(case["expected_layers"]),
        focus_terms=tuple(case["focus_terms"]),
        user_turn=case["user_turn"],
    )
    return [(query.layer, query.query) for query in build_advisor_queries(snapshot, source_need=source_need)]


def search_index(index: CorpusIndex, query: str, *, layer: str | None, top_k: int, backend: str):
    if backend == "bm25":
        return index.search(query, layer=layer, top_k=top_k)
    if backend == "vector":
        return index.vector_search(query, layer=layer, top_k=top_k)
    if backend == "hybrid":
        return index.hybrid_search(query, layer=layer, top_k=top_k)
    raise ValueError(f"unknown retrieval backend: {backend}")


def score_cases(cases: list[dict[str, Any]], top_k: int, query_source: str, retrieval_backend: str) -> list[QueryResult]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    results: list[QueryResult] = []

    for case in cases:
        expected_layers = tuple(case["expected_layers"])
        query_specs = query_specs_for_case(case, query_source)
        search_results = []
        seen_chunk_ids = set()
        for layer, query in query_specs:
            for result in search_index(index, query, layer=layer, top_k=top_k, backend=retrieval_backend):
                if result.chunk.id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(result.chunk.id)
                search_results.append(result)

        returned_ids = tuple(result.chunk.id for result in search_results[:top_k])
        returned_layers = [set(result.chunk.layers) for result in search_results[:top_k]]
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
                query_source=query_source,
                retrieval_backend=retrieval_backend,
                queries=tuple(query for _layer, query in query_specs),
                query_layers=tuple(layer for layer, _query in query_specs),
                expected_layers=expected_layers,
                returned_ids=returned_ids,
                known_useful_rank=known_useful_rank,
                useful_at_3=known_useful_rank is not None and known_useful_rank <= 3,
                useful_at_5=known_useful_rank is not None and known_useful_rank <= 5,
                top1_layer_match=bool(returned_layers) and bool(returned_layers[0] & expected_layer_set),
                any_layer_match_at_5=any(layers & expected_layer_set for layers in returned_layers[:5]),
                focus_term_recall=focus_term_recall(" ".join(query for _layer, query in query_specs), case["focus_terms"]),
            )
        )

    return results


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def render_report(
    cases: list[dict[str, Any]],
    results: list[QueryResult],
    validation_errors: list[str],
    query_source: str,
    retrieval_backend: str,
) -> str:
    source_description = (
        "hand-authored reference queries from the eval cases"
        if query_source == "reference"
        else "queries generated by the current runtime query builder from each snapshot fixture plus the planner-selected source need"
    )
    lines = [
        "# Advisor Search-Query Quality Eval",
        "",
        "## Scope",
        "",
        "This eval covers only turns where source-material search is the correct next action. It does not evaluate whether the agent should search in the first place; that is covered by the next-action classification eval.",
        "",
        f"Query source: `{query_source}` ({source_description}).",
        f"Retrieval backend: `{retrieval_backend}`.",
        "",
        "Reference mode is a reviewer-written seed baseline: it asks whether source-specific queries can retrieve citeable chunks. Generated mode is the product-behavior check for the query builder after the advisor has selected a source need. Backend comparisons should use the same query source and case set.",
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
    query_counter = Counter(query.lower() for result in results for query in result.queries)
    duplicate_queries = {query: count for query, count in query_counter.items() if count > 1}

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
            "| Case | Split | Purpose | Expected Layers | Query Layers | Queries | Top Chunks | Known Useful Rank | Focus Recall |",
            "|---|---|---|---|---|---|---|---:|---:|",
        ]
    )

    for result in results:
        rank = result.known_useful_rank if result.known_useful_rank is not None else "-"
        lines.append(
            "| "
            f"`{result.case_id}` | `{result.split}` | `{result.purpose}` | "
            f"{', '.join(result.expected_layers)} | "
            f"{', '.join(layer or 'none' for layer in result.query_layers) or '-'} | "
            f"{'<br>'.join(result.queries) or '-'} | "
            f"{', '.join(f'`{chunk_id}`' for chunk_id in result.returned_ids) or '-'} | "
            f"{rank} | {result.focus_term_recall:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use reference mode as the source-specific query seed baseline. Use generated mode as the source-need-driven runtime query-generation baseline. Compare retrieval backends only after source-need generation and generated-query quality are strong enough that backend differences are interpretable.",
            "",
            "## Next Work",
            "",
            "Use generated-mode regressions to catch broad queries or duplicate query reuse. The next product eval is whether the acting agent selects the right source need before search.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "advisor_search_query_quality.md")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--query-source",
        choices=("reference", "generated"),
        default="reference",
        help="Use hand-authored reference queries or runtime-generated advisor queries.",
    )
    parser.add_argument(
        "--retrieval-backend",
        choices=("bm25", "vector", "hybrid"),
        default="bm25",
        help="Retrieval backend to evaluate.",
    )
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    results = (
        []
        if validation_errors
        else score_cases(
            cases,
            top_k=args.top_k,
            query_source=args.query_source,
            retrieval_backend=args.retrieval_backend,
        )
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(
            cases,
            results,
            validation_errors,
            query_source=args.query_source,
            retrieval_backend=args.retrieval_backend,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "cases": len(cases),
                "validation_errors": len(validation_errors),
                "scored_cases": len(results),
                "query_source": args.query_source,
                "retrieval_backend": args.retrieval_backend,
                "report": str(args.report.resolve().relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
