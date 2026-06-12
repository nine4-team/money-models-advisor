#!/usr/bin/env python3
"""Compare BM25, vector, and hybrid retrieval on the search-query seed cases."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import eval_search_query_quality as query_eval  # noqa: E402
from money_model_architect.embeddings import EmbeddingError  # noqa: E402
from money_model_architect.vector_store import VectorStoreError  # noqa: E402


BACKENDS = ("bm25", "vector", "hybrid")


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def summarize(results: list[query_eval.QueryResult]) -> dict[str, object]:
    total = len(results)
    misses = [result.case_id for result in results if not result.useful_at_5]
    ranks = [result.known_useful_rank for result in results if result.known_useful_rank is not None]
    total_ms = [result.total_ms for result in results]
    retrieval_ms = [result.retrieval_ms for result in results]
    embedding_ms = [result.embedding_ms for result in results]
    embedding = aggregate_embedding_deltas(results)
    estimated_cost = estimate_embedding_cost(embedding)
    return {
        "cases": total,
        "known_useful_hit_at_3": pct(sum(result.useful_at_3 for result in results), total),
        "known_useful_hit_at_5": pct(sum(result.useful_at_5 for result in results), total),
        "top1_layer_match": pct(sum(result.top1_layer_match for result in results), total),
        "any_expected_layer_at_5": pct(sum(result.any_layer_match_at_5 for result in results), total),
        "mean_known_useful_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "misses_at_5": misses,
        "p50_total_ms": round(statistics.median(total_ms), 3) if total_ms else 0.0,
        "p95_total_ms": round(percentile(total_ms, 95), 3) if total_ms else 0.0,
        "p50_retrieval_ms": round(statistics.median(retrieval_ms), 3) if retrieval_ms else 0.0,
        "p95_retrieval_ms": round(percentile(retrieval_ms, 95), 3) if retrieval_ms else 0.0,
        "p50_embedding_ms": round(statistics.median(embedding_ms), 3) if embedding_ms else 0.0,
        "p95_embedding_ms": round(percentile(embedding_ms, 95), 3) if embedding_ms else 0.0,
        "average_query_count": round(sum(result.query_count for result in results) / total, 2) if total else 0.0,
        "average_variant_count": round(sum(result.variant_count for result in results) / total, 2) if total else 0.0,
        "vector_search_count": sum(result.vector_search_count for result in results),
        "embedding": embedding,
        "estimated_embedding_cost_usd": estimated_cost,
        "estimated_embedding_cost_per_1000_queries_usd": round((estimated_cost / total) * 1000, 8) if total else 0.0,
    }


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = (len(values) - 1) * percentile_value / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def aggregate_embedding_deltas(results: list[query_eval.QueryResult]) -> dict[str, object]:
    totals: dict[str, dict[str, float]] = {}
    model = None
    cache_namespace = None
    cache_dir = None
    for result in results:
        delta = result.embedding_delta or {}
        model = model or delta.get("model")
        cache_namespace = cache_namespace or delta.get("cache_namespace")
        cache_dir = cache_dir or delta.get("cache_dir")
        for purpose, stats in delta.get("by_purpose", {}).items():
            purpose_totals = totals.setdefault(purpose, {})
            for key, value in stats.items():
                if key == "cache_hit_rate":
                    continue
                purpose_totals[key] = purpose_totals.get(key, 0.0) + float(value)

    by_purpose = {}
    for purpose, stats in totals.items():
        hits = stats.get("cache_hits", 0.0)
        misses = stats.get("cache_misses", 0.0)
        total = hits + misses
        by_purpose[purpose] = {
            key: round(value, 3) if key == "elapsed_ms" else int(value)
            for key, value in stats.items()
        }
        by_purpose[purpose]["cache_hit_rate"] = round(hits / total, 4) if total else 1.0

    return {
        "model": model,
        "cache_namespace": cache_namespace,
        "cache_dir": cache_dir,
        "by_purpose": by_purpose,
    }


def estimate_embedding_cost(embedding: dict[str, object]) -> float:
    # Keep this local to the eval report so retrieval behavior never depends on pricing.
    model = embedding.get("model")
    default_prices = {
        "text-embedding-3-small": 0.02,
        "text-embedding-3-large": 0.13,
    }
    cost_per_1m = default_prices.get(str(model), 0.0)
    api_tokens = 0
    for stats in embedding.get("by_purpose", {}).values():
        api_tokens += int(stats.get("estimated_api_input_tokens", 0))
    return round((api_tokens / 1_000_000) * cost_per_1m, 8)


def render_report(
    query_source: str,
    top_k: int,
    vector_store: str,
    namespace_prefix: str,
    target_namespace_source: str,
    max_workers: int,
    summaries: dict[str, dict[str, object]],
    errors: dict[str, str],
    run_metadata: dict[str, dict[str, object]],
) -> str:
    lines = [
        "# Retrieval Backend Comparison",
        "",
        "## Scope",
        "",
        "This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.",
        "",
        f"- Query source: `{query_source}`",
        f"- Top K: `{top_k}`",
        f"- Vector store: `{vector_store}`",
        "- Namespace policy: `source_need_target_namespaces` for vector/hybrid runs; BM25 does not use vector namespaces.",
        f"- Target namespace source: `{target_namespace_source}`",
        f"- Max per-case retrieval workers: `{max_workers}`",
        f"- Namespace prefix: `{namespace_prefix}`",
        "- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.",
        "- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.",
        "",
        "Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.",
        "",
        "## Metrics",
        "",
        "| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for backend in BACKENDS:
        if backend in errors:
            lines.append(f"| `{backend}` | - | - | - | - | - | - | {errors[backend]} |")
            continue
        summary = summaries[backend]
        misses = summary["misses_at_5"]
        lines.append(
            "| "
            f"`{backend}` | "
            f"{summary['cases']} | "
            f"{summary['known_useful_hit_at_3']} | "
            f"{summary['known_useful_hit_at_5']} | "
            f"{summary['top1_layer_match']} | "
            f"{summary['any_expected_layer_at_5']} | "
            f"{summary['mean_known_useful_rank'] if summary['mean_known_useful_rank'] is not None else '-'} | "
            f"{', '.join(f'`{case_id}`' for case_id in misses) if misses else 'none'} |"
        )

    lines.extend(
        [
            "",
            "## Performance And Cost",
            "",
            "| Backend | p50 Total | p95 Total | p50 Retrieval | p95 Retrieval | p50 Embedding | p95 Embedding | Avg Queries | Avg Variants | Vector Searches | Query Cache Hit Rate | Corpus Cache Hit Rate | API Batches | Estimated Cost | Est. Cost / 1K Queries |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for backend in BACKENDS:
        if backend in errors:
            lines.append(f"| `{backend}` | - | - | - | - | - | - | - | - | - | - | - | - | - | - |")
            continue
        summary = summaries[backend]
        query_stats = _purpose_stats(summary, "query")
        corpus_stats = _purpose_stats(summary, "corpus")
        api_batches = int(query_stats.get("api_batches", 0)) + int(corpus_stats.get("api_batches", 0))
        lines.append(
            "| "
            f"`{backend}` | "
            f"{summary['p50_total_ms']} ms | "
            f"{summary['p95_total_ms']} ms | "
            f"{summary['p50_retrieval_ms']} ms | "
            f"{summary['p95_retrieval_ms']} ms | "
            f"{summary['p50_embedding_ms']} ms | "
            f"{summary['p95_embedding_ms']} ms | "
            f"{summary['average_query_count']} | "
            f"{summary['average_variant_count']} | "
            f"{summary['vector_search_count']} | "
            f"{_cache_rate(query_stats)} | "
            f"{_cache_rate(corpus_stats)} | "
            f"{api_batches} | "
            f"${summary['estimated_embedding_cost_usd']:.8f} | "
            f"${summary['estimated_embedding_cost_per_1000_queries_usd']:.8f} |"
        )

    if run_metadata:
        lines.extend(["", "## Cache State", ""])
        for backend in BACKENDS:
            metadata = run_metadata.get(backend, {})
            embedding = metadata.get("embedding") if isinstance(metadata, dict) else None
            if not isinstance(embedding, dict) or not embedding.get("model"):
                continue
            namespaces = metadata.get("namespaces") if isinstance(metadata.get("namespaces"), list) else []
            lines.append(
                f"- `{backend}`: vector store `{metadata.get('vector_store')}`, cache mode `{embedding.get('cache_mode')}`, namespace `{embedding.get('cache_namespace')}`, "
                f"namespace policy `{metadata.get('namespace_policy')}`, "
                f"target namespace source `{metadata.get('target_namespace_source')}`, "
                f"max workers `{metadata.get('max_workers')}`, "
                f"query namespaces `{', '.join(f'`{namespace}`' for namespace in namespaces) if namespaces else 'default'}`, "
                f"query cache complete before run: `{embedding.get('cache_was_complete_for_queries')}`, "
                f"cache dir `{embedding.get('cache_dir')}`."
            )

    lines.extend(
        [
            "",
            "## Dataset",
            "",
        ]
    )
    if summaries:
        any_summary = next(iter(summaries.values()))
        lines.append(f"- Scored cases: {any_summary['cases']}")
    if len(summaries) > 1:
        lines.extend(["", "## Interpretation", ""])
        sorted_hit5 = sorted(
            summaries.items(),
            key=lambda item: (
                _pct_value(item[1]["known_useful_hit_at_5"]),
                -float(item[1]["mean_known_useful_rank"] or 999),
            ),
            reverse=True,
        )
        best_backend, best_summary = sorted_hit5[0]
        lines.append(
            f"- Best eval-slice result by Hit@5 and mean known-useful rank: `{best_backend}` at "
            f"{best_summary['known_useful_hit_at_5']} Hit@5 and mean rank {best_summary['mean_known_useful_rank']}."
        )
        lines.append(
            "- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive."
        )
        lines.append(
            "- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite."
        )
    if errors:
        lines.extend(["", "## Run Notes", ""])
        for backend, error in errors.items():
            lines.append(f"- `{backend}`: {error}")
    lines.append("")
    return "\n".join(lines)


def _purpose_stats(summary: dict[str, object], purpose: str) -> dict[str, object]:
    embedding = summary.get("embedding")
    if not isinstance(embedding, dict):
        return {}
    by_purpose = embedding.get("by_purpose")
    if not isinstance(by_purpose, dict):
        return {}
    stats = by_purpose.get(purpose)
    return stats if isinstance(stats, dict) else {}


def _cache_rate(stats: dict[str, object]) -> str:
    if not stats:
        return "n/a"
    return f"{float(stats.get('cache_hit_rate', 1.0)) * 100:.1f}%"


def _pct_value(value: object) -> float:
    if not isinstance(value, str) or not value.endswith("%"):
        return 0.0
    return float(value[:-1])


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def case_row(result: query_eval.QueryResult, query_source: str, vector_store: str) -> dict[str, object]:
    return {
        "case_id": result.case_id,
        "retriever": result.retrieval_backend,
        "query_source": query_source,
        "vector_store": "n/a" if result.retrieval_backend == "bm25" else vector_store,
        "namespace_policy": "n/a" if result.retrieval_backend == "bm25" else "source_need_target_namespaces",
        "target_namespaces_by_query": [list(namespaces) for namespaces in result.query_target_namespaces],
        "hit_at_3": result.useful_at_3,
        "hit_at_5": result.useful_at_5,
        "rank": result.known_useful_rank,
        "query_count": result.query_count,
        "variant_count": result.variant_count,
        "embedding_inputs_by_variant": [
            {
                "index": index,
                "chars": len(query),
                "query": query,
            }
            for index, query in enumerate(result.queries, 1)
        ],
        "vector_search_count": result.vector_search_count,
        "merged_result_count": result.merged_result_count,
        "query_build_ms": result.query_build_ms,
        "embedding_ms": result.embedding_ms,
        "retrieval_ms": result.retrieval_ms,
        "merge_rank_ms": result.merge_rank_ms,
        "total_ms": result.total_ms,
        "top_chunk_ids": list(result.returned_ids),
        "embedding_delta": result.embedding_delta or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases.jsonl")
    parser.add_argument("--query-source", choices=("reference", "generated", "generated_variants"), default="generated")
    parser.add_argument(
        "--query-variants",
        type=Path,
        default=ROOT / "evals" / "advisor_query_variants_v2.jsonl",
        help="JSONL candidate query variants keyed by case_id; used only with --query-source generated_variants.",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "retrieval_backend_comparison.md")
    parser.add_argument("--vector-store", choices=("local", "pinecone"), default="local")
    parser.add_argument("--namespace-prefix", default="money-models")
    parser.add_argument(
        "--target-namespace-source",
        choices=("none", "expected_layers"),
        default="none",
        help="How to populate SourceNeed.target_namespaces for vector/hybrid namespace experiments. 'expected_layers' is an oracle condition.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Maximum per-case retrieval workers. Use >1 for hosted vector stores to avoid serial query-variant latency.",
    )
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--cases-jsonl", type=Path)
    parser.add_argument(
        "--require-all-backends",
        action="store_true",
        help="Exit nonzero when vector or hybrid cannot run, for strict backend-comparison gates.",
    )
    args = parser.parse_args()

    cases = query_eval.load_jsonl(args.cases)
    validation_errors = query_eval.validate_cases(cases)
    variants_by_case: dict[str, list[str]] = {}
    if not validation_errors and args.query_source == "generated_variants":
        try:
            variants_by_case = query_eval.load_variant_rows(args.query_variants)
        except ValueError as exc:
            validation_errors.append(str(exc))
        missing_variant_cases = [
            case["case_id"]
            for case in cases
            if case["case_id"] not in variants_by_case
        ]
        if missing_variant_cases:
            validation_errors.append("query variants missing cases: " + ", ".join(missing_variant_cases))
    if validation_errors:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(["# Retrieval Backend Comparison", "", *validation_errors, ""]), encoding="utf-8")
        print(json.dumps({"validation_errors": len(validation_errors), "report": str(args.report)}, indent=2))
        return 1

    summaries: dict[str, dict[str, object]] = {}
    run_metadata: dict[str, dict[str, object]] = {}
    case_rows: list[dict[str, object]] = []
    errors: dict[str, str] = {}
    for backend in BACKENDS:
        try:
            results, metadata = query_eval.score_cases_with_metrics(
                cases,
                top_k=args.top_k,
                query_source=args.query_source,
                retrieval_backend=backend,
                variants_by_case=variants_by_case,
                vector_store_name=args.vector_store,
                namespace_prefix=args.namespace_prefix,
                target_namespace_source=args.target_namespace_source,
                max_workers=args.max_workers,
            )
        except (EmbeddingError, VectorStoreError) as exc:
            errors[backend] = str(exc)
            continue
        summaries[backend] = summarize(results)
        run_metadata[backend] = metadata
        case_rows.extend(case_row(result, args.query_source, args.vector_store) for result in results)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(
            args.query_source,
            args.top_k,
            args.vector_store,
            args.namespace_prefix,
            args.target_namespace_source,
            args.max_workers,
            summaries,
            errors,
            run_metadata,
        ),
        encoding="utf-8",
    )
    summary_json = args.summary_json or args.report.with_name(f"{args.report.stem}_summary.json")
    cases_jsonl = args.cases_jsonl or args.report.with_name(f"{args.report.stem}_cases.jsonl")
    summary_json.write_text(
        json.dumps(
            {
                "cases": len(cases),
                "query_source": args.query_source,
                "vector_store": args.vector_store,
                "namespace_policy": "source_need_target_namespaces",
                "target_namespace_source": args.target_namespace_source,
                "namespace_prefix": args.namespace_prefix,
                "max_workers": args.max_workers,
                "top_k": args.top_k,
                "summaries": summaries,
                "errors": errors,
                "run_metadata": run_metadata,
                "split_counts": dict(sorted(Counter(case["split"] for case in cases).items())),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    cases_jsonl.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in case_rows),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "cases": len(cases),
                "query_source": args.query_source,
                "query_variants": str(args.query_variants.resolve().relative_to(ROOT)) if args.query_source == "generated_variants" else None,
                "vector_store": args.vector_store,
                "namespace_policy": "source_need_target_namespaces",
                "target_namespace_source": args.target_namespace_source,
                "namespace_prefix": args.namespace_prefix,
                "max_workers": args.max_workers,
                "summaries": summaries,
                "errors": errors,
                "report": display_path(args.report),
                "summary_json": display_path(summary_json),
                "cases_jsonl": display_path(cases_jsonl),
                "split_counts": dict(sorted(Counter(case["split"] for case in cases).items())),
            },
            indent=2,
        )
    )
    return 1 if args.require_all_backends and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
