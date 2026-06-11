#!/usr/bin/env python3
"""Score source-search query quality seed cases.

This eval only applies after next-action classification has already decided
that `search_source_material` is appropriate for the turn.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.advisor_queries import SourceNeed, build_advisor_queries  # noqa: E402
from money_model_architect.embeddings import OpenAIEmbeddingClient  # noqa: E402
from money_model_architect.retrieval import CorpusIndex, SearchResult  # noqa: E402
from money_model_architect.snapshot import BusinessSnapshot  # noqa: E402
from money_model_architect.vector_store import PineconeVectorStore, VectorStore, selected_vector_store_name  # noqa: E402


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
    query_reasons: tuple[str, ...]
    query_layers: tuple[str | None, ...]
    expected_layers: tuple[str, ...]
    returned_ids: tuple[str, ...]
    known_useful_rank: int | None
    useful_at_3: bool
    useful_at_5: bool
    top1_layer_match: bool
    any_layer_match_at_5: bool
    focus_term_recall: float
    query_build_ms: float = 0.0
    retrieval_ms: float = 0.0
    merge_rank_ms: float = 0.0
    total_ms: float = 0.0
    embedding_ms: float = 0.0
    query_count: int = 0
    variant_count: int = 0
    vector_search_count: int = 0
    merged_result_count: int = 0
    embedding_delta: dict[str, Any] | None = None


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


def load_variant_rows(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    rows = load_jsonl(path)
    variants_by_case: dict[str, list[str]] = {}
    for row in rows:
        case_id = row.get("case_id")
        variants = row.get("query_variants")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{path}: every row must have a non-empty case_id")
        if not isinstance(variants, list) or not variants or not all(isinstance(item, str) and item.strip() for item in variants):
            raise ValueError(f"{path}: {case_id} query_variants must be a non-empty list of strings")
        variants_by_case[case_id] = variants
    return variants_by_case


def query_specs_for_case(
    case: dict[str, Any],
    query_source: str,
    variants_by_case: dict[str, list[str]] | None = None,
) -> list[tuple[str | None, str, str]]:
    if query_source == "reference":
        expected_layers = case["expected_layers"]
        layer = expected_layers[0] if len(expected_layers) == 1 else None
        return [(layer, case["reference_query"], "Reviewer-authored source-specific reference query.")]

    snapshot = BusinessSnapshot.load(ROOT / case["snapshot_fixture_path"])
    query_variants = ()
    if query_source == "generated_variants":
        query_variants = tuple((variants_by_case or {}).get(case["case_id"], ()))
    source_need = SourceNeed(
        intent=case["retrieval_purpose"],
        layers=tuple(case["expected_layers"]),
        focus_terms=tuple(case["focus_terms"]),
        user_turn=case["user_turn"],
        query_variants=query_variants,
    )
    return [(query.layer, query.query, query.reason) for query in build_advisor_queries(snapshot, source_need=source_need)]


def search_index(
    index: CorpusIndex,
    query: str,
    *,
    layer: str | None,
    top_k: int,
    backend: str,
    embedding_client: Any | None = None,
    vector_store: VectorStore | None = None,
    vector_store_name: str = "local",
):
    if backend == "bm25":
        return index.search(query, layer=layer, top_k=top_k)
    if backend == "vector":
        return index.vector_search(
            query,
            layer=layer,
            top_k=top_k,
            embedding_client=embedding_client,
            vector_store=vector_store,
            vector_store_name=vector_store_name,
        )
    if backend == "hybrid":
        return index.hybrid_search(
            query,
            layer=layer,
            top_k=top_k,
            embedding_client=embedding_client,
            vector_store=vector_store,
            vector_store_name=vector_store_name,
        )
    raise ValueError(f"unknown retrieval backend: {backend}")


def fuse_query_results(query_result_sets: list[list[SearchResult]], top_k: int, rrf_k: int = 60) -> list[SearchResult]:
    chunks_by_id = {}
    fused_scores: dict[str, float] = defaultdict(float)
    for result_set in query_result_sets:
        for rank, result in enumerate(result_set, 1):
            chunks_by_id[result.chunk.id] = result.chunk
            fused_scores[result.chunk.id] += 1 / (rrf_k + rank)
    fused = [
        SearchResult(chunk=chunks_by_id[chunk_id], score=score)
        for chunk_id, score in fused_scores.items()
    ]
    fused.sort(key=lambda result: result.score, reverse=True)
    return fused[:top_k]


def score_cases(
    cases: list[dict[str, Any]],
    top_k: int,
    query_source: str,
    retrieval_backend: str,
    variants_by_case: dict[str, list[str]] | None = None,
    vector_store_name: str = "local",
) -> list[QueryResult]:
    return score_cases_with_metrics(
        cases,
        top_k=top_k,
        query_source=query_source,
        retrieval_backend=retrieval_backend,
        variants_by_case=variants_by_case,
        vector_store_name=vector_store_name,
    )[0]


def score_cases_with_metrics(
    cases: list[dict[str, Any]],
    top_k: int,
    query_source: str,
    retrieval_backend: str,
    variants_by_case: dict[str, list[str]] | None = None,
    vector_store_name: str = "local",
) -> tuple[list[QueryResult], dict[str, Any]]:
    index_started = time.perf_counter()
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    index_ms = (time.perf_counter() - index_started) * 1000
    embedding_client = OpenAIEmbeddingClient() if retrieval_backend in {"vector", "hybrid"} else None
    selected_store = selected_vector_store_name(vector_store_name)
    vector_store = PineconeVectorStore.from_env() if retrieval_backend in {"vector", "hybrid"} and selected_store == "pinecone" else None
    query_texts = all_query_texts(cases, query_source, variants_by_case=variants_by_case)
    corpus_cache_before = embedding_client.cache_presence(index.corpus_embedding_texts()) if embedding_client else None
    query_cache_before = embedding_client.cache_presence(query_texts) if embedding_client else None
    results: list[QueryResult] = []

    for case in cases:
        case_started = time.perf_counter()
        expected_layers = tuple(case["expected_layers"])
        query_started = time.perf_counter()
        query_specs = query_specs_for_case(case, query_source, variants_by_case=variants_by_case)
        query_build_ms = (time.perf_counter() - query_started) * 1000
        query_result_sets = []
        embedding_before = _embedding_stats_snapshot(embedding_client)
        retrieval_started = time.perf_counter()
        for layer, query, _reason in query_specs:
            query_result_sets.append(
                search_index(
                    index,
                    query,
                    layer=layer,
                    top_k=max(top_k * 5, top_k),
                    backend=retrieval_backend,
                    embedding_client=embedding_client,
                    vector_store=vector_store,
                    vector_store_name=selected_store,
                )
            )
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000
        embedding_after = _embedding_stats_snapshot(embedding_client)
        merge_started = time.perf_counter()
        search_results = fuse_query_results(query_result_sets, top_k=top_k)
        merge_rank_ms = (time.perf_counter() - merge_started) * 1000
        embedding_delta = _embedding_stats_delta(embedding_before, embedding_after)

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
                query_source=query_source,
                retrieval_backend=retrieval_backend,
                queries=tuple(query for _layer, query, _reason in query_specs),
                query_reasons=tuple(reason for _layer, _query, reason in query_specs),
                query_layers=tuple(layer for layer, _query, _reason in query_specs),
                expected_layers=expected_layers,
                returned_ids=returned_ids,
                known_useful_rank=known_useful_rank,
                useful_at_3=known_useful_rank is not None and known_useful_rank <= 3,
                useful_at_5=known_useful_rank is not None and known_useful_rank <= 5,
                top1_layer_match=bool(returned_layers) and bool(returned_layers[0] & expected_layer_set),
                any_layer_match_at_5=any(layers & expected_layer_set for layers in returned_layers[:5]),
                focus_term_recall=focus_term_recall(" ".join(query for _layer, query, _reason in query_specs), case["focus_terms"]),
                query_build_ms=round(query_build_ms, 3),
                retrieval_ms=round(retrieval_ms, 3),
                merge_rank_ms=round(merge_rank_ms, 3),
                total_ms=round((time.perf_counter() - case_started) * 1000, 3),
                embedding_ms=round(_embedding_elapsed_ms(embedding_delta), 3),
                query_count=len(query_specs),
                variant_count=max(0, len(query_specs) - 1) if query_source == "generated_variants" else 0,
                vector_search_count=len(query_specs) if retrieval_backend in {"vector", "hybrid"} else 0,
                merged_result_count=len({result.chunk.id for result_set in query_result_sets for result in result_set}),
                embedding_delta=embedding_delta,
            )
        )

    run_metadata = {
        "index_ms": round(index_ms, 3),
        "chunks": len(index.chunks),
        "cache_mode": "current",
        "vector_store": selected_store if retrieval_backend in {"vector", "hybrid"} else "n/a",
        "embedding": _embedding_run_metadata(embedding_client, corpus_cache_before, query_cache_before),
    }
    return results, run_metadata


def all_query_texts(
    cases: list[dict[str, Any]],
    query_source: str,
    variants_by_case: dict[str, list[str]] | None = None,
) -> list[str]:
    texts: list[str] = []
    for case in cases:
        texts.extend(query for _layer, query, _reason in query_specs_for_case(case, query_source, variants_by_case=variants_by_case))
    return texts


def _embedding_stats_snapshot(client: Any | None) -> dict[str, Any]:
    stats = getattr(client, "stats", None)
    if stats is None:
        return {}
    return stats.to_dict()


def _embedding_stats_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if not after:
        return {}
    before_by_purpose = before.get("by_purpose", {}) if before else {}
    after_by_purpose = after.get("by_purpose", {})
    by_purpose: dict[str, dict[str, float | int]] = {}
    for purpose, after_stats in after_by_purpose.items():
        before_stats = before_by_purpose.get(purpose, {})
        by_purpose[purpose] = {
            key: round(after_stats.get(key, 0) - before_stats.get(key, 0), 3)
            if isinstance(after_stats.get(key, 0), float)
            else after_stats.get(key, 0) - before_stats.get(key, 0)
            for key in (
                "cache_hits",
                "cache_misses",
                "api_batches",
                "api_inputs",
                "input_chars",
                "api_input_chars",
                "estimated_api_input_tokens",
                "elapsed_ms",
            )
        }
        total = by_purpose[purpose]["cache_hits"] + by_purpose[purpose]["cache_misses"]
        by_purpose[purpose]["cache_hit_rate"] = round(by_purpose[purpose]["cache_hits"] / total, 4) if total else 1.0
    return {
        "model": after.get("model"),
        "cache_namespace": after.get("cache_namespace"),
        "cache_dir": after.get("cache_dir"),
        "by_purpose": by_purpose,
    }


def _embedding_elapsed_ms(delta: dict[str, Any]) -> float:
    return sum(stats.get("elapsed_ms", 0.0) for stats in delta.get("by_purpose", {}).values())


def _embedding_run_metadata(
    client: OpenAIEmbeddingClient | None,
    corpus_cache_before: dict[str, int | bool] | None,
    query_cache_before: dict[str, int | bool] | None,
) -> dict[str, Any]:
    if client is None:
        return {
            "model": None,
            "cache_namespace": None,
            "cache_dir": None,
            "cache_mode": "n/a",
            "corpus_cache_before": None,
            "query_cache_before": None,
            "estimated_embedding_cost_usd": 0.0,
        }
    return {
        "model": client.model,
        "cache_namespace": f"openai/{client.model}",
        "cache_dir": str(client.cache_dir),
        "cache_mode": "current",
        "corpus_cache_before": corpus_cache_before,
        "query_cache_before": query_cache_before,
        "cache_was_complete_for_queries": bool(query_cache_before and query_cache_before.get("complete")),
        "estimated_embedding_cost_usd": round(client.estimated_api_cost_usd(), 8),
        "stats": client.stats.to_dict(),
    }


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
        else (
            "queries generated by the current runtime query builder from each snapshot fixture, planner-selected source need, and agent-generated query variants"
            if query_source == "generated_variants"
            else "queries generated by the current runtime query builder from each snapshot fixture plus the planner-selected source need"
        )
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
        "Reference mode is a reviewer-written seed baseline: it asks whether source-specific queries can retrieve citeable chunks. Generated mode is the deterministic fallback query-builder baseline after the advisor has selected a source need. Generated-variants mode adds constrained agent-written query variants ahead of the fallback query. Backend comparisons should use the same query source and case set.",
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
            f"- Average queries per case: {(sum(len(result.queries) for result in results) / total) if total else 0:.2f}",
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
            "Use reference mode as the source-specific query seed baseline. Use generated mode as the deterministic fallback runtime baseline. Use generated-variants mode to test whether constrained agent-authored query variants improve retrieval before changing the production search path.",
            "",
            "## Next Work",
            "",
            "Use generated-mode regressions to catch broad queries or duplicate query reuse. Use generated-variants misses to tune the query-variant schema or agent guidance without changing golden relevance labels.",
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
        choices=("reference", "generated", "generated_variants"),
        default="reference",
        help="Use hand-authored reference queries or runtime-generated advisor queries.",
    )
    parser.add_argument(
        "--query-variants",
        type=Path,
        default=ROOT / "evals" / "advisor_query_variants_v2.jsonl",
        help="JSONL candidate query variants keyed by case_id; used only with --query-source generated_variants.",
    )
    parser.add_argument(
        "--retrieval-backend",
        choices=("bm25", "vector", "hybrid"),
        default="bm25",
        help="Retrieval backend to evaluate.",
    )
    parser.add_argument(
        "--vector-store",
        choices=("local", "pinecone"),
        default="local",
        help="Vector storage backend for vector/hybrid retrieval.",
    )
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    validation_errors = validate_cases(cases)
    variants_by_case: dict[str, list[str]] = {}
    if not validation_errors and args.query_source == "generated_variants":
        try:
            variants_by_case = load_variant_rows(args.query_variants)
        except ValueError as exc:
            validation_errors.append(str(exc))
        missing_variant_cases = [
            case["case_id"]
            for case in cases
            if case["case_id"] not in variants_by_case
        ]
        if missing_variant_cases:
            validation_errors.append(
                "query variants missing cases: " + ", ".join(missing_variant_cases)
            )
    results = (
        []
        if validation_errors
        else score_cases(
            cases,
            top_k=args.top_k,
            query_source=args.query_source,
            retrieval_backend=args.retrieval_backend,
            variants_by_case=variants_by_case,
            vector_store_name=args.vector_store,
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
                "vector_store": args.vector_store,
                "query_variants": str(args.query_variants.resolve().relative_to(ROOT)) if args.query_source == "generated_variants" else None,
                "report": str(args.report.resolve().relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
