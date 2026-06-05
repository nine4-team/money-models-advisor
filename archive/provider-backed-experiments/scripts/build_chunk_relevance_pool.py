#!/usr/bin/env python3
"""Build a blind chunk relevance review pool from candidate retrievers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def stable_order_key(query_id: str, chunk_id: str) -> str:
    return hashlib.sha256(f"{query_id}:{chunk_id}".encode("utf-8")).hexdigest()


def bm25_items(index: CorpusIndex, records: list[dict[str, Any]], top_k: int) -> dict[str, list[dict[str, Any]]]:
    by_record = {}
    for record in records:
        results = index.search(record["query"], layer=record.get("target_layer_hint"), top_k=top_k)
        by_record[record["id"]] = [
            {"chunk_id": result.chunk.id, "chapter": result.chunk.chapter, "score": result.score}
            for result in results
        ]
    return by_record


def dense_items(
    index: CorpusIndex,
    records: list[dict[str, Any]],
    top_k: int,
    client: OpenAIEmbeddingClient,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    chunk_vectors, chunk_usage = client.embed_many([chunk.text for chunk in index.chunks])
    query_vectors, query_usage = client.embed_many([record["query"] for record in records])
    by_record = {}
    for record, query_vector in zip(records, query_vectors, strict=True):
        scored = []
        for chunk, chunk_vector in zip(index.chunks, chunk_vectors, strict=True):
            if record.get("target_layer_hint") and record["target_layer_hint"] not in chunk.layers:
                continue
            scored.append(
                {
                    "chunk_id": chunk.id,
                    "chapter": chunk.chapter,
                    "score": cosine_similarity(query_vector, chunk_vector),
                }
            )
        scored.sort(reverse=True, key=lambda item: item["score"])
        by_record[record["id"]] = scored[:top_k]
    usage = {
        "model": client.model,
        "dimensions": client.dimensions,
        "prompt_tokens": chunk_usage.prompt_tokens + query_usage.prompt_tokens,
        "total_tokens": chunk_usage.total_tokens + query_usage.total_tokens,
        "api_requests": chunk_usage.api_requests + query_usage.api_requests,
        "cache_hits": chunk_usage.cache_hits + query_usage.cache_hits,
    }
    return by_record, usage


def hybrid_items(
    bm25_by_record: dict[str, list[dict[str, Any]]],
    dense_by_record: dict[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    top_k: int,
    rrf_k: int = 60,
) -> dict[str, list[dict[str, Any]]]:
    by_record = {}
    for record in records:
        scores: dict[str, float] = defaultdict(float)
        chunks: dict[str, dict[str, Any]] = {}
        first_seen: dict[str, int] = {}
        for rank, item in enumerate(bm25_by_record[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chunks[chunk_id] = {"chunk_id": chunk_id, "chapter": item["chapter"]}
            first_seen.setdefault(chunk_id, rank)
        for rank, item in enumerate(dense_by_record[record["id"]], start=1):
            chunk_id = item["chunk_id"]
            scores[chunk_id] += 1 / (rrf_k + rank)
            chunks[chunk_id] = {"chunk_id": chunk_id, "chapter": item["chapter"]}
            first_seen.setdefault(chunk_id, rank)
        ordered = sorted(scores, key=lambda chunk_id: (scores[chunk_id], -first_seen[chunk_id]), reverse=True)
        by_record[record["id"]] = [
            {**chunks[chunk_id], "score": scores[chunk_id]}
            for chunk_id in ordered[:top_k]
        ]
    return by_record


def add_variant(
    pooled: dict[tuple[str, str], dict[str, Any]],
    records_by_id: dict[str, dict[str, Any]],
    variant: str,
    results_by_record: dict[str, list[dict[str, Any]]],
) -> None:
    for query_id, items in results_by_record.items():
        record = records_by_id[query_id]
        for rank, item in enumerate(items, start=1):
            key = (query_id, item["chunk_id"])
            row = pooled.setdefault(
                key,
                {
                    "id": f"{query_id}::{item['chunk_id']}",
                    "query_id": query_id,
                    "query": record["query"],
                    "query_type": record["query_type"],
                    "target_layer_hint": record.get("target_layer_hint"),
                    "candidate_chapters": record.get("candidate_chapters", []),
                    "chunk_id": item["chunk_id"],
                    "chunk_chapter": item["chapter"],
                    "retrieved_by": [],
                    "relevance": None,
                    "status": "unreviewed",
                    "notes": "",
                },
            )
            row["retrieved_by"].append({"variant": variant, "rank": rank, "score": round(item["score"], 6)})


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Chunk Relevance Pool",
        "",
        "## Purpose",
        "",
        "This file records the candidate chunk pool for blind relevance review. Each row is a query/chunk pair collected from candidate retrievers over the realistic query set.",
        "",
        "The reviewer should not use retriever provenance while labeling. Provenance is stored in the JSONL so metrics can be computed after review.",
        "",
        "## Build Summary",
        "",
        f"- Query set: `{run['query_set']}`",
        f"- Queries: {run['query_count']}",
        f"- Unique query/chunk pairs: {run['pool_count']}",
        f"- Retriever top-k: {run['top_k']}",
        f"- Fusion top-k: {run['fusion_k']}",
        f"- Output: `{run['pool_path']}`",
        "",
        "## Variants",
        "",
        "| Variant | Queries Covered | Retrieved Rows |",
        "|---|---:|---:|",
    ]
    for variant in run["variants"]:
        lines.append(f"| `{variant['name']}` | {variant['queries_covered']} | {variant['retrieved_rows']} |")
    if run.get("usage"):
        usage = run["usage"]
        lines.extend(
            [
                "",
                "## Cost Note",
                "",
                f"Embedding usage: {usage.get('total_tokens', 0)} API tokens, {usage.get('api_requests', 0)} API requests, {usage.get('cache_hits', 0)} cache hits.",
            ]
        )
    lines.extend(
        [
            "",
            "## Label Rubric",
            "",
            "| Label | Meaning |",
            "|---:|---|",
            "| 0 | The chunk is not useful for answering this query. |",
            "| 1 | The chunk is partially useful or background context, but not enough by itself. |",
            "| 2 | The chunk directly supports a good answer to the query. |",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build chunk relevance review pool")
    parser.add_argument("--queries", type=Path, default=ROOT / "evals" / "realistic_queries.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.jsonl")
    parser.add_argument("--chunking", default="heading-aware")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fusion-k", type=int, default=20)
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--dimensions", type=int)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "embeddings.sqlite3")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "chunk_relevance_pool.md")
    args = parser.parse_args()

    load_env_file(ROOT / ".env.local")
    load_env_file(ROOT / ".env")

    records = load_jsonl(args.queries)
    records_by_id = {record["id"]: record for record in records}
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)

    started = time.perf_counter()
    bm25_top = bm25_items(index, records, args.top_k)
    bm25_fusion = bm25_items(index, records, args.fusion_k)

    variants = [
        {"name": "bm25", "queries_covered": len(bm25_top), "retrieved_rows": sum(len(items) for items in bm25_top.values())}
    ]
    pooled: dict[tuple[str, str], dict[str, Any]] = {}
    add_variant(pooled, records_by_id, "bm25", bm25_top)

    usage = None
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required to build dense/hybrid review pool")

    client = OpenAIEmbeddingClient(model=args.embedding_model, dimensions=args.dimensions, cache_path=args.cache)
    dense_top, dense_usage = dense_items(index, records, args.top_k, client)
    dense_fusion, fusion_usage = dense_items(index, records, args.fusion_k, client)
    hybrid_top = hybrid_items(bm25_fusion, dense_fusion, records, args.top_k)
    usage = {
        "model": client.model,
        "dimensions": client.dimensions,
        "prompt_tokens": dense_usage["prompt_tokens"] + fusion_usage["prompt_tokens"],
        "total_tokens": dense_usage["total_tokens"] + fusion_usage["total_tokens"],
        "api_requests": dense_usage["api_requests"] + fusion_usage["api_requests"],
        "cache_hits": dense_usage["cache_hits"] + fusion_usage["cache_hits"],
    }
    for name, result in (("dense-openai", dense_top), ("hybrid-rrf", hybrid_top)):
        add_variant(pooled, records_by_id, name, result)
        variants.append({"name": name, "queries_covered": len(result), "retrieved_rows": sum(len(items) for items in result.values())})

    rows = sorted(pooled.values(), key=lambda row: (row["query_id"], stable_order_key(row["query_id"], row["chunk_id"])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, rows)
    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
        "query_set": str(args.queries.relative_to(ROOT)),
        "query_count": len(records),
        "pool_count": len(rows),
        "top_k": args.top_k,
        "fusion_k": args.fusion_k,
        "pool_path": str(args.output.relative_to(ROOT)),
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "variants": variants,
        "usage": usage,
    }
    write_report(run, args.report)
    print(json.dumps(run, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
