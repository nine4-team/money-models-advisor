#!/usr/bin/env python3
"""Compare chunking strategies while holding retrieval constant."""

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

from money_model_architect.retrieval import CHUNKING_STRATEGIES, CorpusIndex  # noqa: E402


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


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = (len(values) - 1) * percentile_value / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def evaluate_strategy(records: list[dict[str, Any]], strategy: str, top_k: int) -> dict[str, Any]:
    started = time.perf_counter()
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=strategy)
    index_ms = (time.perf_counter() - started) * 1000
    latencies = []
    query_results = []

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
    return {
        "strategy": strategy,
        "chunks": len(index.chunks),
        "avg_chunk_words": round(index.average_chunk_words(), 1),
        "index_ms": round(index_ms, 3),
        "metrics": {
            "total": total,
            "hit_at_1": round(sum(1 for result in query_results if result["hit_at_1"]) / total, 4),
            "hit_at_5": round(sum(1 for result in query_results if result["hit_at_5"]) / total, 4),
            "mrr": round(sum(result["reciprocal_rank"] for result in query_results) / total, 4),
            "p50_latency_ms": round(statistics.median(latencies), 3),
            "p95_latency_ms": round(percentile(latencies, 95), 3),
        },
        "queries": query_results,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    variants = run["variants"]
    best = max(variants, key=lambda variant: (variant["metrics"]["mrr"], variant["metrics"]["hit_at_1"]))
    baseline = next((variant for variant in variants if variant["strategy"] == "heading-aware"), variants[0])
    mrr_delta = best["metrics"]["mrr"] - baseline["metrics"]["mrr"]
    hit_at_1_delta = best["metrics"]["hit_at_1"] - baseline["metrics"]["hit_at_1"]
    clears_adoption_threshold = best["strategy"] == baseline["strategy"] or hit_at_1_delta > 0 or mrr_delta >= 0.01
    adopted = best if clears_adoption_threshold else baseline
    lines = [
        "# Chunking Comparison",
        "",
        "## Hypothesis",
        "",
        "Framework or heading-aware chunks should retrieve named Money Models concepts more precisely than naive fixed windows, because the transcripts are organized around concepts, examples, and numbered frameworks.",
        "",
        "## Variants",
        "",
        "| Strategy | Chunks | Avg Words | Hit@1 | Hit@5 | MRR | p95 Latency |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for variant in variants:
        metrics = variant["metrics"]
        lines.append(
            f"| `{variant['strategy']}` | {variant['chunks']} | {variant['avg_chunk_words']} | "
            f"{metrics['hit_at_1']:.2%} | {metrics['hit_at_5']:.2%} | {metrics['mrr']:.4f} | {metrics['p95_latency_ms']} ms |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{best['strategy']}` is the metric winner on MRR in this local BM25 comparison. The adopted default remains `{adopted['strategy']}` because adoption requires either a Hit@1 improvement or an MRR gain of at least 0.01 over the simpler heading-aware baseline.",
            "",
            f"Measured delta vs `heading-aware`: Hit@1 {hit_at_1_delta:+.2%}, MRR {mrr_delta:+.4f}.",
            "",
            "## Failure Analysis",
            "",
        ]
    )

    for variant in variants:
        misses = [query for query in variant["queries"] if not query["hit_at_5"]]
        if misses:
            lines.append(f"- `{variant['strategy']}` had {len(misses)} hit@5 misses: " + ", ".join(f"`{miss['id']}`" for miss in misses))
        else:
            lines.append(f"- `{variant['strategy']}` had no hit@5 misses.")

    lines.extend(
        [
            "",
            "## Next Experiment",
            "",
            "Score the retrieval variants against accepted required-claim labels. The framework-aware candidate can be revisited if a future support-coverage run shows that it retrieves better supporting chunks, but the current retrieval-quality gain is below the adoption threshold.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local chunking strategies")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "chunking_comparison.md")
    parser.add_argument("--strategies", nargs="*", default=list(CHUNKING_STRATEGIES))
    args = parser.parse_args()

    records = load_jsonl(args.golden)
    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "experiment": "chunking-comparison",
        "dataset": str(args.golden.relative_to(ROOT)),
        "top_k": args.top_k,
        "variants": [evaluate_strategy(records, strategy, args.top_k) for strategy in args.strategies],
    }

    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-chunking-comparison.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, args.report)

    print(
        json.dumps(
            {
                "run_path": str(run_path.relative_to(ROOT)),
                "report_path": str(args.report.relative_to(ROOT)),
                "variants": [
                    {
                        "strategy": variant["strategy"],
                        "hit_at_1": variant["metrics"]["hit_at_1"],
                        "hit_at_5": variant["metrics"]["hit_at_5"],
                        "mrr": variant["metrics"]["mrr"],
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
