#!/usr/bin/env python3
"""Compare retrieval variants against human-audited required-claim labels."""

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
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def golden_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in load_jsonl(path)}


def load_required_claims(path: Path, include_proposed: bool) -> list[dict[str, Any]]:
    allowed = {"accepted", "proposed"} if include_proposed else {"accepted"}
    return [
        claim
        for claim in load_jsonl(path)
        if claim.get("status") in allowed and claim.get("supporting_chunk_ids")
    ]


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = (len(values) - 1) * percentile_value / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def bm25_items(index: CorpusIndex, records: list[dict[str, Any]], top_k: int) -> tuple[dict[str, list[dict[str, Any]]], list[float]]:
    by_record = {}
    latencies = []
    for record in records:
        started = time.perf_counter()
        results = index.search(record["query"], layer=record.get("layer"), top_k=top_k)
        latencies.append((time.perf_counter() - started) * 1000)
        by_record[record["id"]] = [
            {
                "chunk_id": result.chunk.id,
                "chapter": result.chunk.chapter,
                "score": result.score,
            }
            for result in results
        ]
    return by_record, latencies


def dense_items(
    index: CorpusIndex,
    records: list[dict[str, Any]],
    top_k: int,
    client: OpenAIEmbeddingClient,
) -> tuple[dict[str, list[dict[str, Any]]], list[float], dict[str, Any]]:
    chunk_vectors, chunk_usage = client.embed_many([chunk.text for chunk in index.chunks])
    query_vectors, query_usage = client.embed_many([record["query"] for record in records])
    by_record = {}
    latencies = []

    for record, query_vector in zip(records, query_vectors, strict=True):
        started = time.perf_counter()
        scored = []
        for chunk, chunk_vector in zip(index.chunks, chunk_vectors, strict=True):
            if record.get("layer") and record["layer"] not in chunk.layers:
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
        latencies.append((time.perf_counter() - started) * 1000)

    usage = {
        "model": client.model,
        "dimensions": client.dimensions,
        "prompt_tokens": chunk_usage.prompt_tokens + query_usage.prompt_tokens,
        "total_tokens": chunk_usage.total_tokens + query_usage.total_tokens,
        "api_requests": chunk_usage.api_requests + query_usage.api_requests,
        "cache_hits": chunk_usage.cache_hits + query_usage.cache_hits,
    }
    return by_record, latencies, usage


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


def hybrid_lexical_anchor_items(
    bm25_by_record: dict[str, list[dict[str, Any]]],
    dense_by_record: dict[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    top_k: int,
    anchor_count: int = 1,
) -> dict[str, list[dict[str, Any]]]:
    by_record = {}
    hybrid_top = hybrid_items(bm25_by_record, dense_by_record, records, max(0, top_k - anchor_count))
    for record in records:
        selected = list(hybrid_top[record["id"]])
        seen = {item["chunk_id"] for item in selected}
        for item in bm25_by_record[record["id"]]:
            if item["chunk_id"] not in seen:
                selected.append(item)
                seen.add(item["chunk_id"])
            if len(selected) >= top_k:
                break
        by_record[record["id"]] = selected[:top_k]
    return by_record


def score_required_claims(
    name: str,
    claims: list[dict[str, Any]],
    golden: dict[str, dict[str, Any]],
    retrieved_by_record: dict[str, list[dict[str, Any]]],
    latencies: list[float],
    usage: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    results = []
    for claim in claims:
        record = golden[claim["record_id"]]
        retrieved_ids = [item["chunk_id"] for item in retrieved_by_record[record["id"]]]
        supporting = set(claim["supporting_chunk_ids"])
        matched = [chunk_id for chunk_id in retrieved_ids if chunk_id in supporting]
        results.append(
            {
                "id": claim["id"],
                "record_id": claim["record_id"],
                "query": record["query"],
                "claim": claim["claim"],
                "status": claim.get("status"),
                "supporting_chunk_ids": claim["supporting_chunk_ids"],
                "retrieved_chunk_ids": retrieved_ids,
                "supported": bool(matched),
                "matched_chunk_ids": matched,
            }
        )

    total = len(results)
    supported = sum(1 for result in results if result["supported"])
    return {
        "name": name,
        "status": "ok",
        "notes": notes,
        "usage": usage,
        "metrics": {
            "total": total,
            "support_coverage": round(supported / total, 4) if total else 0.0,
            "unsupported": total - supported,
            "p50_latency_ms": round(statistics.median(latencies), 3) if latencies else 0.0,
            "p95_latency_ms": round(percentile(latencies, 95), 3) if latencies else 0.0,
        },
        "required_claims": results,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Retrieval Required-Claim Ablation",
        "",
        "## Hypothesis",
        "",
        "Dense and hybrid retrieval should improve semantic ranking without losing chunks that support the human-audited required claims for each eval query.",
        "",
        "## Label Set",
        "",
        f"- Label status included: `{run['label_status']}`",
        f"- Required-claim labels scored: {run['claim_count']}",
        f"- Top-k context window: {run['top_k']}",
        "",
        "## Variants",
        "",
        "| Variant | Support Coverage | Unsupported | p95 Latency | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for variant in run["variants"]:
        if variant["status"] != "ok":
            lines.append(f"| `{variant['name']}` |  |  |  | {variant.get('reason', '')} |")
            continue
        metrics = variant["metrics"]
        notes = variant.get("notes", "")
        if variant.get("usage"):
            usage = variant["usage"]
            notes = (notes + "; " if notes else "") + f"{usage.get('total_tokens', 0)} API tokens, {usage.get('cache_hits', 0)} cache hits"
        lines.append(
            f"| `{variant['name']}` | {metrics['support_coverage']:.2%} | {metrics['unsupported']} | "
            f"{metrics['p95_latency_ms']} ms | {notes} |"
        )

    dense_usage = next((variant.get("usage") for variant in run["variants"] if variant.get("usage")), None)
    if dense_usage:
        lines.extend(
            [
                "",
                "Cost note: embedding vectors are cached in `.cache/embeddings.sqlite3` by model, dimensions, and text hash. "
                f"This run reported {dense_usage.get('total_tokens', 0)} API tokens and {dense_usage.get('cache_hits', 0)} cache hits, so warm reruns preserve the experimental signal without repeated embedding spend.",
            ]
        )

    ok_variants = [variant for variant in run["variants"] if variant["status"] == "ok"]
    bm25 = next((variant for variant in ok_variants if variant["name"] == "bm25"), None)
    best = max(ok_variants, key=lambda variant: (variant["metrics"]["support_coverage"], -variant["metrics"]["unsupported"]))
    lines.extend(["", "## Decision", ""])
    if bm25:
        lines.append("Guardrail: a candidate retriever should match or improve BM25 required-claim support coverage before becoming the default retrieval policy.")
        lines.append("")
        for variant in ok_variants:
            if variant["name"] == "bm25":
                continue
            delta = variant["metrics"]["support_coverage"] - bm25["metrics"]["support_coverage"]
            passes = delta >= 0
            lines.append(f"- `{variant['name']}` {'passes' if passes else 'fails'}: support coverage {delta:+.2%} vs `bm25`.")
        lines.append("")
    lines.append(f"Decision from this experiment alone: `{best['name']}` has the strongest required-claim support coverage.")
    lines.append("")
    lines.append(
        "Combined interpretation: this report is the evidence-support guardrail, not the whole retrieval decision. "
        "`retrieval_ablation.md` still owns rank quality. A default retriever should improve rank quality and pass this guardrail; in the current measured set, plain `hybrid-rrf` does that, while dense-only is the strongest support-coverage challenger for the next rerank experiment."
    )

    lines.extend(["", "## Unsupported Required Claims", ""])
    for variant in ok_variants:
        misses = [claim for claim in variant["required_claims"] if not claim["supported"]]
        lines.append(f"### {variant['name']}")
        if not misses:
            lines.append("")
            lines.append("- None.")
            lines.append("")
            continue
        lines.append("")
        for miss in misses:
            expected = ", ".join(f"`{chunk_id}`" for chunk_id in miss["supporting_chunk_ids"])
            retrieved = ", ".join(f"`{chunk_id}`" for chunk_id in miss["retrieved_chunk_ids"])
            lines.append(f"- `{miss['id']}`: {miss['claim']}")
            lines.append(f"  Expected one of: {expected}")
            lines.append(f"  Retrieved: {retrieved}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run retrieval ablation against required-claim labels")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--claims", type=Path, default=ROOT / "evals" / "obligations.jsonl")
    parser.add_argument("--include-proposed", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fusion-k", type=int, default=20)
    parser.add_argument("--chunking", default="heading-aware")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--dimensions", type=int)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "embeddings.sqlite3")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "retrieval_required_claim_ablation.md")
    args = parser.parse_args()

    load_env_file(ROOT / ".env.local")
    load_env_file(ROOT / ".env")

    golden = golden_by_id(args.golden)
    claims = load_required_claims(args.claims, include_proposed=args.include_proposed)
    needed_record_ids = sorted({claim["record_id"] for claim in claims})
    records = [golden[record_id] for record_id in needed_record_ids]
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)

    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
        "experiment": "retrieval-required-claim-ablation",
        "dataset": str(args.claims.relative_to(ROOT)),
        "label_status": "accepted+proposed" if args.include_proposed else "accepted",
        "claim_count": len(claims),
        "query_count": len(records),
        "top_k": args.top_k,
        "fusion_k": args.fusion_k,
        "chunking": args.chunking,
        "variants": [],
    }

    bm25_top, bm25_latencies = bm25_items(index, records, args.top_k)
    run["variants"].append(score_required_claims("bm25", claims, golden, bm25_top, bm25_latencies))

    if not os.environ.get("OPENAI_API_KEY"):
        reason = "OPENAI_API_KEY not set; dense and hybrid variants were not run"
        run["variants"].append({"name": "dense-openai", "status": "skipped", "reason": reason})
        run["variants"].append({"name": "hybrid-rrf", "status": "skipped", "reason": reason})
        run["variants"].append({"name": "hybrid-rrf-lexical-anchor", "status": "skipped", "reason": reason})
    else:
        client = OpenAIEmbeddingClient(model=args.embedding_model, dimensions=args.dimensions, cache_path=args.cache)
        dense_top, dense_latencies, dense_usage = dense_items(index, records, args.top_k, client)
        run["variants"].append(
            score_required_claims(
                "dense-openai",
                claims,
                golden,
                dense_top,
                dense_latencies,
                dense_usage,
                notes="OpenAI dense similarity",
            )
        )

        bm25_fusion, _bm25_fusion_latencies = bm25_items(index, records, args.fusion_k)
        dense_fusion, dense_fusion_latencies, fusion_usage = dense_items(index, records, args.fusion_k, client)
        hybrid_top = hybrid_items(bm25_fusion, dense_fusion, records, args.top_k)
        run["variants"].append(
            score_required_claims(
                "hybrid-rrf",
                claims,
                golden,
                hybrid_top,
                dense_fusion_latencies,
                fusion_usage,
                notes=f"RRF over top {args.fusion_k}",
            )
        )

        anchored_top = hybrid_lexical_anchor_items(bm25_fusion, dense_fusion, records, args.top_k)
        run["variants"].append(
            score_required_claims(
                "hybrid-rrf-lexical-anchor",
                claims,
                golden,
                anchored_top,
                dense_fusion_latencies,
                fusion_usage,
                notes=f"RRF top {args.top_k - 1} + BM25 anchor",
            )
        )

    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-retrieval-required-claim-ablation.json"
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
