#!/usr/bin/env python3
"""Compare BM25, OpenAI dense embeddings, and hybrid RRF retrieval."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.embeddings import OpenAIEmbeddingClient, cosine_similarity  # noqa: E402
from money_model_architect.env import load_env_file  # noqa: E402
from money_model_architect.retrieval import CorpusIndex  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def expected_rank(chapters: list[str], expected: set[str]) -> int | None:
    for index, chapter in enumerate(chapters, start=1):
        if chapter in expected:
            return index
    return None


def reciprocal_rank(chapters: list[str], expected: set[str]) -> float:
    rank = expected_rank(chapters, expected)
    return 0.0 if rank is None else 1 / rank


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = (len(values) - 1) * percentile_value / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def evaluate_rankings(records: list[dict[str, Any]], rankings: dict[str, list[str]], latencies: list[float]) -> dict[str, Any]:
    query_results = []
    for record in records:
        chapters = rankings[record["id"]]
        expected = set(record["must_chapters"])
        rank = expected_rank(chapters, expected)
        query_results.append(
            {
                "id": record["id"],
                "layer": record.get("layer"),
                "expected_chapters": record["must_chapters"],
                "retrieved_chapters": chapters,
                "rank": rank,
                "hit_at_1": rank == 1,
                "hit_at_5": rank is not None and rank <= 5,
                "reciprocal_rank": reciprocal_rank(chapters, expected),
            }
        )

    total = len(query_results)
    return {
        "metrics": {
            "total": total,
            "hit_at_1": round(sum(1 for result in query_results if result["hit_at_1"]) / total, 4),
            "hit_at_5": round(sum(1 for result in query_results if result["hit_at_5"]) / total, 4),
            "mrr": round(sum(result["reciprocal_rank"] for result in query_results) / total, 4),
            "p50_latency_ms": round(statistics.median(latencies), 3) if latencies else 0.0,
            "p95_latency_ms": round(percentile(latencies, 95), 3) if latencies else 0.0,
        },
        "queries": query_results,
    }


def bm25_rankings(index: CorpusIndex, records: list[dict[str, Any]], top_k: int) -> tuple[dict[str, list[str]], list[float], dict[str, list[dict[str, Any]]]]:
    rankings = {}
    items = {}
    latencies = []
    for record in records:
        started = time.perf_counter()
        results = index.search(record["query"], layer=record.get("layer"), top_k=top_k)
        latencies.append((time.perf_counter() - started) * 1000)
        rankings[record["id"]] = [result.chunk.chapter for result in results]
        items[record["id"]] = [
            {
                "chunk_id": result.chunk.id,
                "chapter": result.chunk.chapter,
                "score": result.score,
            }
            for result in results
        ]
    return rankings, latencies, items


def dense_rankings(
    index: CorpusIndex,
    records: list[dict[str, Any]],
    top_k: int,
    client: OpenAIEmbeddingClient,
) -> tuple[dict[str, list[str]], list[float], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    chunk_texts = [chunk.text for chunk in index.chunks]
    chunk_vectors, chunk_usage = client.embed_many(chunk_texts)
    query_vectors, query_usage = client.embed_many([record["query"] for record in records])
    rankings = {}
    items = {}
    latencies = []

    for record, query_vector in zip(records, query_vectors, strict=True):
        started = time.perf_counter()
        scored = []
        for chunk, chunk_vector in zip(index.chunks, chunk_vectors, strict=True):
            if record.get("layer") and record["layer"] not in chunk.layers:
                continue
            scored.append((cosine_similarity(query_vector, chunk_vector), chunk.id, chunk.chapter))
        scored.sort(reverse=True, key=lambda item: item[0])
        rankings[record["id"]] = [chapter for _score, _chunk_id, chapter in scored[:top_k]]
        items[record["id"]] = [
            {
                "chunk_id": chunk_id,
                "chapter": chapter,
                "score": score,
            }
            for score, chunk_id, chapter in scored[:top_k]
        ]
        latencies.append((time.perf_counter() - started) * 1000)

    usage = {
        "model": client.model,
        "dimensions": client.dimensions,
        "prompt_tokens": chunk_usage.prompt_tokens + query_usage.prompt_tokens,
        "total_tokens": chunk_usage.total_tokens + query_usage.total_tokens,
        "api_requests": chunk_usage.api_requests + query_usage.api_requests,
        "cache_hits": chunk_usage.cache_hits + query_usage.cache_hits,
    }
    return rankings, latencies, items, usage


def hybrid_rankings(
    bm25_full: dict[str, list[dict[str, Any]]],
    dense_full: dict[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    top_k: int,
    rrf_k: int = 60,
) -> dict[str, list[str]]:
    rankings = {}
    for record in records:
        scores: dict[str, float] = defaultdict(float)
        chapters: dict[str, str] = {}
        first_seen: dict[str, int] = {}
        for rank, item in enumerate(bm25_full[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chapters[chunk_id] = item["chapter"]
            first_seen.setdefault(chunk_id, rank)
        for rank, item in enumerate(dense_full[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chapters[chunk_id] = item["chapter"]
            first_seen.setdefault(chunk_id, rank)
        ordered = sorted(scores, key=lambda chunk_id: (scores[chunk_id], -first_seen[chunk_id]), reverse=True)
        rankings[record["id"]] = [chapters[chunk_id] for chunk_id in ordered[:top_k]]
    return rankings


def hybrid_lexical_anchor_rankings(
    bm25_full: dict[str, list[dict[str, Any]]],
    dense_full: dict[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    top_k: int,
    anchor_count: int = 1,
    rrf_k: int = 60,
) -> dict[str, list[str]]:
    rankings = {}
    hybrid_top_k = max(0, top_k - anchor_count)
    for record in records:
        scores: dict[str, float] = defaultdict(float)
        chapters: dict[str, str] = {}
        first_seen: dict[str, int] = {}
        for rank, item in enumerate(bm25_full[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chapters[chunk_id] = item["chapter"]
            first_seen.setdefault(chunk_id, rank)
        for rank, item in enumerate(dense_full[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chapters[chunk_id] = item["chapter"]
            first_seen.setdefault(chunk_id, rank)

        ordered = sorted(scores, key=lambda chunk_id: (scores[chunk_id], -first_seen[chunk_id]), reverse=True)
        selected: list[str] = []
        seen: set[str] = set()
        for chunk_id in ordered:
            selected.append(chunk_id)
            seen.add(chunk_id)
            if len(selected) >= hybrid_top_k:
                break

        for item in bm25_full[record["id"]]:
            chunk_id = item["chunk_id"]
            if chunk_id not in seen:
                selected.append(chunk_id)
                seen.add(chunk_id)
            if len(selected) >= top_k:
                break

        rankings[record["id"]] = [chapters[chunk_id] for chunk_id in selected[:top_k]]
    return rankings


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Retrieval Ablation",
        "",
        "## Hypothesis",
        "",
        "Dense embeddings and hybrid retrieval should improve semantic or paraphrased query retrieval over the BM25 control, but they must earn their additional API cost and implementation complexity.",
        "",
        "## Variants",
        "",
        "| Variant | Status | Hit@1 | Hit@5 | MRR | p95 Latency | Notes |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for variant in run["variants"]:
        if variant["status"] != "ok":
            lines.append(f"| `{variant['name']}` | {variant['status']} |  |  |  |  | {variant.get('reason', '')} |")
            continue
        metrics = variant["metrics"]
        notes = variant.get("notes", "")
        lines.append(
            f"| `{variant['name']}` | ok | {metrics['hit_at_1']:.2%} | {metrics['hit_at_5']:.2%} | "
            f"{metrics['mrr']:.4f} | {metrics['p95_latency_ms']} ms | {notes} |"
        )

    dense_usage = next(
        (variant.get("usage") for variant in run["variants"] if variant["name"] == "dense-openai" and variant.get("usage")),
        None,
    )
    if dense_usage:
        lines.extend(
            [
                "",
                "Cost note: embedding experiments use deterministic vectors cached in `.cache/embeddings.sqlite3`, keyed by model and text hash. "
                f"This run reported {dense_usage.get('total_tokens', 0)} API tokens and {dense_usage.get('cache_hits', 0)} cache hits for `dense-openai`; "
                "the first uncached run pays to embed corpus/query texts, while warm reruns avoid duplicate embedding calls.",
            ]
        )

    ok_variants = [variant for variant in run["variants"] if variant["status"] == "ok"]
    best = max(ok_variants, key=lambda variant: (variant["metrics"]["mrr"], variant["metrics"]["hit_at_1"]))
    tied_best = [
        variant
        for variant in ok_variants
        if variant["metrics"]["mrr"] == best["metrics"]["mrr"] and variant["metrics"]["hit_at_1"] == best["metrics"]["hit_at_1"]
    ]
    bm25 = next(variant for variant in ok_variants if variant["name"] == "bm25")
    mrr_delta = best["metrics"]["mrr"] - bm25["metrics"]["mrr"]
    hit_delta = best["metrics"]["hit_at_1"] - bm25["metrics"]["hit_at_1"]
    best_names = ", ".join(f"`{variant['name']}`" for variant in tied_best)

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"{best_names} {'are tied metric winners' if len(tied_best) > 1 else 'is the metric winner'} in this run. Adopt a non-BM25 default only if it improves Hit@1 or increases MRR by at least 0.01 without regressing accepted required-claim support coverage.",
            "",
            f"Measured delta vs `bm25`: Hit@1 {hit_delta:+.2%}, MRR {mrr_delta:+.4f}.",
            "",
            "## Failure Analysis",
            "",
        ]
    )
    for variant in ok_variants:
        misses = [query for query in variant["queries"] if not query["hit_at_5"]]
        if misses:
            lines.append(f"- `{variant['name']}` had {len(misses)} hit@5 misses: " + ", ".join(f"`{miss['id']}`" for miss in misses))
        else:
            lines.append(f"- `{variant['name']}` had no hit@5 misses.")

    lines.extend(
        [
            "",
            "## Next Experiment",
            "",
            "If dense or hybrid improves retrieval, run required-claim support coverage across the winning retrieval variant. If not, keep BM25 locally and defer dense retrieval until paraphrase-heavy eval records are expanded.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run retrieval ablation")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fusion-k", type=int, default=20)
    parser.add_argument("--chunking", default="heading-aware")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--dimensions", type=int)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "embeddings.sqlite3")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "retrieval_ablation.md")
    args = parser.parse_args()
    load_env_file(ROOT / ".env.local")
    load_env_file(ROOT / ".env")

    records = load_jsonl(args.golden)
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)
    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "experiment": "retrieval-ablation",
        "dataset": str(args.golden.relative_to(ROOT)),
        "top_k": args.top_k,
        "fusion_k": args.fusion_k,
        "chunking": args.chunking,
        "variants": [],
    }

    bm25_top, bm25_latencies, _bm25_items = bm25_rankings(index, records, args.top_k)
    bm25_eval = evaluate_rankings(records, bm25_top, bm25_latencies)
    run["variants"].append({"name": "bm25", "status": "ok", **bm25_eval})

    api_key_available = bool(os.environ.get("OPENAI_API_KEY"))
    if not api_key_available:
        reason = "OPENAI_API_KEY not set; dense and hybrid variants were not run"
        run["variants"].append({"name": "dense-openai", "status": "skipped", "reason": reason})
        run["variants"].append({"name": "hybrid-rrf", "status": "skipped", "reason": reason})
        run["variants"].append({"name": "hybrid-rrf-lexical-anchor", "status": "skipped", "reason": reason})
    else:
        client = OpenAIEmbeddingClient(
            model=args.embedding_model,
            dimensions=args.dimensions,
            cache_path=args.cache,
        )
        dense_top, dense_latencies, _dense_items, usage = dense_rankings(index, records, args.top_k, client)
        dense_eval = evaluate_rankings(records, dense_top, dense_latencies)
        run["variants"].append({"name": "dense-openai", "status": "ok", "usage": usage, "notes": f"{usage['total_tokens']} API tokens, {usage['cache_hits']} cache hits", **dense_eval})

        _bm25_fusion, _bm25_fusion_latencies, bm25_fusion_items = bm25_rankings(index, records, args.fusion_k)
        _dense_fusion, dense_fusion_latencies, dense_fusion_items, usage_fusion = dense_rankings(index, records, args.fusion_k, client)
        hybrid = hybrid_rankings(bm25_fusion_items, dense_fusion_items, records, args.top_k)
        hybrid_eval = evaluate_rankings(records, hybrid, dense_fusion_latencies)
        run["variants"].append({"name": "hybrid-rrf", "status": "ok", "usage": usage_fusion, "notes": f"RRF over top {args.fusion_k}", **hybrid_eval})

        anchored = hybrid_lexical_anchor_rankings(bm25_fusion_items, dense_fusion_items, records, args.top_k)
        anchored_eval = evaluate_rankings(records, anchored, dense_fusion_latencies)
        run["variants"].append(
            {
                "name": "hybrid-rrf-lexical-anchor",
                "status": "ok",
                "usage": usage_fusion,
                "notes": f"RRF top {args.top_k - 1} + BM25 anchor",
                **anchored_eval,
            }
        )

    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-retrieval-ablation.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, args.report)

    print(
        json.dumps(
            {
                "run_path": str(run_path.relative_to(ROOT)),
                "report_path": str(args.report.relative_to(ROOT)),
                "variants": [
                    {
                        "name": variant["name"],
                        "status": variant["status"],
                        "metrics": variant.get("metrics"),
                        "reason": variant.get("reason"),
                    }
                    for variant in run["variants"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
