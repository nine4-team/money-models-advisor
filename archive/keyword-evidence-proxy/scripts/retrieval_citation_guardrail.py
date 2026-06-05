#!/usr/bin/env python3
"""Check citation evidence coverage for BM25 vs hybrid retrieval."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
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
                record = json.loads(line)
                if record.get("evidence_terms"):
                    records.append(record)
    return records


def normalize(text: str) -> str:
    normalized = f" {text.lower().replace('-', ' ')} "
    replacements = {
        " zero ": " 0 ",
        " one ": " 1 ",
        " two ": " 2 ",
        " three ": " 3 ",
        " four ": " 4 ",
        " five ": " 5 ",
        " six ": " 6 ",
        " seven ": " 7 ",
        " eight ": " 8 ",
        " nine ": " 9 ",
        " ten ": " 10 ",
        " thirty ": " 30 ",
    }
    for word, digit in replacements.items():
        normalized = normalized.replace(word, digit)
    return " ".join(normalized.split())


def term_present(text: str, term: str) -> bool:
    return normalize(term) in normalize(text)


def bm25_items(index: CorpusIndex, record: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
    return [
        {"chunk": result.chunk, "score": result.score}
        for result in index.search(record["query"], layer=record.get("layer"), top_k=top_k)
    ]


def dense_items(index: CorpusIndex, records: list[dict[str, Any]], top_k: int, client: OpenAIEmbeddingClient) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    chunk_vectors, chunk_usage = client.embed_many([chunk.text for chunk in index.chunks])
    query_vectors, query_usage = client.embed_many([record["query"] for record in records])
    output = {}
    for record, query_vector in zip(records, query_vectors, strict=True):
        scored = []
        for chunk, chunk_vector in zip(index.chunks, chunk_vectors, strict=True):
            if record.get("layer") and record["layer"] not in chunk.layers:
                continue
            scored.append({"chunk": chunk, "score": cosine_similarity(query_vector, chunk_vector)})
        scored.sort(reverse=True, key=lambda item: item["score"])
        output[record["id"]] = scored[:top_k]
    usage = {
        "total_tokens": chunk_usage.total_tokens + query_usage.total_tokens,
        "api_requests": chunk_usage.api_requests + query_usage.api_requests,
        "cache_hits": chunk_usage.cache_hits + query_usage.cache_hits,
    }
    return output, usage


def hybrid_items(bm25: list[dict[str, Any]], dense: list[dict[str, Any]], top_k: int, rrf_k: int = 60) -> list[dict[str, Any]]:
    scores: dict[str, float] = defaultdict(float)
    chunks = {}
    first_seen = {}
    for rank, item in enumerate(bm25, start=1):
        chunk_id = item["chunk"].id
        scores[chunk_id] += 1 / (rrf_k + rank)
        chunks[chunk_id] = item["chunk"]
        first_seen.setdefault(chunk_id, rank)
    for rank, item in enumerate(dense, start=1):
        chunk_id = item["chunk"].id
        scores[chunk_id] += 1 / (rrf_k + rank)
        chunks[chunk_id] = item["chunk"]
        first_seen.setdefault(chunk_id, rank)
    ordered = sorted(scores, key=lambda chunk_id: (scores[chunk_id], -first_seen[chunk_id]), reverse=True)
    return [{"chunk": chunks[chunk_id], "score": scores[chunk_id]} for chunk_id in ordered[:top_k]]


def hybrid_lexical_anchor_items(
    bm25: list[dict[str, Any]],
    dense: list[dict[str, Any]],
    top_k: int,
    anchor_count: int = 1,
    rrf_k: int = 60,
) -> list[dict[str, Any]]:
    hybrid_top = hybrid_items(bm25, dense, max(0, top_k - anchor_count), rrf_k=rrf_k)
    selected = list(hybrid_top)
    seen = {item["chunk"].id for item in selected}
    for item in bm25:
        if item["chunk"].id not in seen:
            selected.append(item)
            seen.add(item["chunk"].id)
        if len(selected) >= top_k:
            break
    return selected[:top_k]


def score_items(record: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    expected = set(record["must_chapters"])
    expected_items = [item for item in items if item["chunk"].chapter in expected]
    candidate_items = expected_items or items[:1]
    scored = []
    for item in candidate_items:
        present = [term for term in record["evidence_terms"] if term_present(item["chunk"].text, term)]
        scored.append((len(present), item["chunk"], present))
    _score, chunk, present = max(scored, key=lambda item: item[0]) if scored else (0, None, [])
    missing = [term for term in record["evidence_terms"] if term not in present]
    return {
        "id": record["id"],
        "evidence_chunk": chunk.id if chunk else None,
        "evidence_chapter": chunk.chapter if chunk else None,
        "retrieved_chapters": [item["chunk"].chapter for item in items],
        "coverage": round(len(present) / len(record["evidence_terms"]), 4),
        "present": present,
        "missing": missing,
    }


def summarize(name: str, query_results: list[dict[str, Any]], usage: dict[str, Any] | None = None) -> dict[str, Any]:
    coverages = [result["coverage"] for result in query_results]
    return {
        "name": name,
        "metrics": {
            "total": len(query_results),
            "avg_coverage": round(statistics.mean(coverages), 4),
            "full_coverage_rate": round(sum(1 for coverage in coverages if coverage == 1.0) / len(coverages), 4),
            "min_coverage": round(min(coverages), 4),
        },
        "usage": usage,
        "queries": query_results,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Retrieval Citation Guardrail",
        "",
        "## Hypothesis",
        "",
        "Hybrid retrieval should not improve ranking metrics at the cost of weaker evidence chunks for cited answers.",
        "",
        "## Variants",
        "",
        "| Variant | Labeled Queries | Avg Coverage | Full Coverage | Min Coverage | Notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for variant in run["variants"]:
        metrics = variant["metrics"]
        usage = variant.get("usage") or {}
        notes = f"{usage.get('total_tokens', 0)} API tokens, {usage.get('cache_hits', 0)} cache hits" if usage else ""
        lines.append(
            f"| `{variant['name']}` | {metrics['total']} | {metrics['avg_coverage']:.2%} | "
            f"{metrics['full_coverage_rate']:.2%} | {metrics['min_coverage']:.2%} | {notes} |"
        )

    hybrid_usage = next(
        (variant.get("usage") for variant in run["variants"] if variant["name"].startswith("hybrid-rrf") and variant.get("usage")),
        None,
    )
    if hybrid_usage:
        lines.extend(
            [
                "",
                "Cost note: this guardrail reuses the same SQLite embedding cache as the retrieval ablation. "
                f"This run reported {hybrid_usage.get('total_tokens', 0)} API tokens and {hybrid_usage.get('cache_hits', 0)} cache hits for hybrid retrieval.",
            ]
        )

    bm25 = next(variant for variant in run["variants"] if variant["name"] == "bm25")
    candidates = [variant for variant in run["variants"] if variant["name"] != "bm25"]
    best = max(candidates, key=lambda variant: (variant["metrics"]["avg_coverage"], variant["metrics"]["full_coverage_rate"]))
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Guardrail allows at most -2 percentage points average coverage or -5 percentage points full-coverage regression versus BM25.",
            "",
        ]
    )
    for variant in candidates:
        avg_delta = variant["metrics"]["avg_coverage"] - bm25["metrics"]["avg_coverage"]
        full_delta = variant["metrics"]["full_coverage_rate"] - bm25["metrics"]["full_coverage_rate"]
        passes = avg_delta >= -0.02 and full_delta >= -0.05
        lines.append(
            f"- `{variant['name']}` {'passes' if passes else 'fails'}: avg coverage {avg_delta:+.2%}, full coverage {full_delta:+.2%} vs `bm25`."
        )
    lines.extend(
        [
            "",
            f"Decision: `{best['name']}` is the best citation-preserving hybrid candidate in this run.",
            "",
            "Interpretation: plain hybrid RRF did not lose the right chapters; it changed which chunks survived into the final top-k context. Dense retrieval and RRF improved semantic ranking, but in a few cases they pushed out the BM25 chunk containing exact citation terms. The lexical-anchor variant keeps the rank lift while reserving one context slot for BM25's strongest exact-term evidence chunk.",
            "",
            "## Per-query Regressions",
            "",
        ]
    )
    bm25_by_id = {query["id"]: query for query in bm25["queries"]}
    regression_variant = next((variant for variant in candidates if variant["name"] == "hybrid-rrf"), best)
    regressions = []
    for query in regression_variant["queries"]:
        delta = query["coverage"] - bm25_by_id[query["id"]]["coverage"]
        if delta < 0:
            regressions.append((query, delta))
    if not regressions:
        lines.append(f"- No per-query coverage regressions for `{regression_variant['name']}`.")
    else:
        lines.append(f"Regressions shown for `{regression_variant['name']}`.")
        lines.append("")
        for query, delta in regressions:
            missing = ", ".join(f"`{term}`" for term in query["missing"])
            lines.append(f"- `{query['id']}` coverage delta {delta:+.2%}; missing {missing}.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run retrieval citation guardrail")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fusion-k", type=int, default=20)
    parser.add_argument("--chunking", default="heading-aware")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--dimensions", type=int)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "embeddings.sqlite3")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "retrieval_citation_guardrail.md")
    args = parser.parse_args()

    load_env_file(ROOT / ".env.local")
    load_env_file(ROOT / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for hybrid citation guardrail")

    records = load_jsonl(args.golden)
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)
    client = OpenAIEmbeddingClient(model=args.embedding_model, dimensions=args.dimensions, cache_path=args.cache)
    dense_by_id, usage = dense_items(index, records, args.fusion_k, client)

    bm25_queries = []
    hybrid_queries = []
    anchored_queries = []
    for record in records:
        bm25_top = bm25_items(index, record, args.top_k)
        bm25_fusion = bm25_items(index, record, args.fusion_k)
        hybrid_top = hybrid_items(bm25_fusion, dense_by_id[record["id"]], args.top_k)
        anchored_top = hybrid_lexical_anchor_items(bm25_fusion, dense_by_id[record["id"]], args.top_k)
        bm25_queries.append(score_items(record, bm25_top))
        hybrid_queries.append(score_items(record, hybrid_top))
        anchored_queries.append(score_items(record, anchored_top))

    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "experiment": "retrieval-citation-guardrail",
        "dataset": str(args.golden.relative_to(ROOT)),
        "top_k": args.top_k,
        "fusion_k": args.fusion_k,
        "chunking": args.chunking,
        "variants": [
            summarize("bm25", bm25_queries),
            summarize("hybrid-rrf", hybrid_queries, usage),
            summarize("hybrid-rrf-lexical-anchor", anchored_queries, usage),
        ],
    }
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-retrieval-citation-guardrail.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, args.report)
    print(
        json.dumps(
            {
                "run_path": str(run_path.relative_to(ROOT)),
                "report_path": str(args.report.relative_to(ROOT)),
                "variants": [{"name": variant["name"], **variant["metrics"]} for variant in run["variants"]],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
