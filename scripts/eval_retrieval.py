#!/usr/bin/env python3
"""Evaluate local corpus retrieval and write reproducible run artifacts."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import CorpusIndex  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def reciprocal_rank(chapters: list[str], expected: set[str]) -> float:
    for index, chapter in enumerate(chapters, start=1):
        if chapter in expected:
            return 1 / index
    return 0.0


def expected_rank(chapters: list[str], expected: set[str]) -> int | None:
    for index, chapter in enumerate(chapters, start=1):
        if chapter in expected:
            return index
    return None


def evaluate(records: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
    started = time.perf_counter()
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts")
    index_ms = (time.perf_counter() - started) * 1000

    query_results = []
    latencies = []

    for record in records:
        query_started = time.perf_counter()
        results = index.search(record["query"], layer=record.get("layer"), top_k=top_k)
        latency_ms = (time.perf_counter() - query_started) * 1000
        latencies.append(latency_ms)

        chapters = [result.chunk.chapter for result in results]
        expected = set(record["must_chapters"])
        rank = expected_rank(chapters, expected)
        query_results.append(
            {
                "id": record["id"],
                "query": record["query"],
                "layer": record.get("layer"),
                "expected_chapters": record["must_chapters"],
                "retrieved_chapters": chapters,
                "rank": rank,
                "hit_at_1": rank == 1,
                "hit_at_5": rank is not None and rank <= 5,
                "reciprocal_rank": reciprocal_rank(chapters, expected),
                "latency_ms": round(latency_ms, 3),
            }
        )

    total = len(query_results)
    hit_at_1 = sum(1 for result in query_results if result["hit_at_1"]) / total
    hit_at_5 = sum(1 for result in query_results if result["hit_at_5"]) / total
    mrr = sum(result["reciprocal_rank"] for result in query_results) / total

    return {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "variant": "local-bm25-heading-aware",
        "dataset": "evals/golden.jsonl",
        "top_k": top_k,
        "index": {
            "chunks": len(index.chunks),
            "index_ms": round(index_ms, 3),
        },
        "metrics": {
            "total": total,
            "hit_at_1": round(hit_at_1, 4),
            "hit_at_5": round(hit_at_5, 4),
            "mrr": round(mrr, 4),
            "p50_latency_ms": round(statistics.median(latencies), 3),
            "p95_latency_ms": round(percentile(latencies, 95), 3),
        },
        "queries": query_results,
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


def write_report(run: dict[str, Any], path: Path) -> None:
    failures = [query for query in run["queries"] if not query["hit_at_5"]]
    metrics = run["metrics"]
    lines = [
        "# Local Retrieval Baseline",
        "",
        "## Hypothesis",
        "",
        "A lightweight local BM25-style retriever over heading-aware transcript chunks should provide a runnable baseline for the five-layer taxonomy.",
        "",
        "## Variant",
        "",
        f"- `{run['variant']}`",
        f"- Dataset: `{run['dataset']}`",
        f"- Top-k: `{run['top_k']}`",
        f"- Chunks indexed: `{run['index']['chunks']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total queries | {metrics['total']} |",
        f"| Hit@1 | {metrics['hit_at_1']:.2%} |",
        f"| Hit@5 | {metrics['hit_at_5']:.2%} |",
        f"| MRR | {metrics['mrr']:.4f} |",
        f"| p50 retrieval latency | {metrics['p50_latency_ms']} ms |",
        f"| p95 retrieval latency | {metrics['p95_latency_ms']} ms |",
        "",
        "## Per-query Results",
        "",
        "| ID | Layer | Expected | Rank | Top retrieved |",
        "|---|---|---|---:|---|",
    ]

    for query in run["queries"]:
        rank = query["rank"] if query["rank"] is not None else "miss"
        expected = ", ".join(query["expected_chapters"])
        top = ", ".join(query["retrieved_chapters"][:3])
        lines.append(f"| `{query['id']}` | `{query['layer']}` | {expected} | {rank} | {top} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use this as the local baseline. Future chunking, embedding, hybrid retrieval, and reranking experiments must beat this run on retrieval quality while staying inside latency and complexity guardrails.",
            "",
            "## Failure Analysis",
            "",
        ]
    )

    if failures:
        for failure in failures:
            lines.append(
                f"- `{failure['id']}` missed expected chapters {failure['expected_chapters']} and retrieved {failure['retrieved_chapters'][:5]}."
            )
    else:
        lines.append("- No hit@5 failures in this run.")

    lines.extend(
        [
            "",
            "## Next Experiment",
            "",
            "Run the chunking comparison so the baseline can be tested against fixed-window and framework-aware variants.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local transcript retrieval")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "local_retrieval_baseline.md")
    args = parser.parse_args()

    run = evaluate(load_jsonl(args.golden), top_k=args.top_k)
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    run_path = args.runs_dir / f"{run['run_id']}-{run['variant']}.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, args.report)

    summary = {
        "run_path": str(run_path.relative_to(ROOT)),
        "report_path": str(args.report.relative_to(ROOT)),
        "metrics": run["metrics"],
    }
    print(json.dumps(summary, indent=2))
    return 0 if run["metrics"]["hit_at_5"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
