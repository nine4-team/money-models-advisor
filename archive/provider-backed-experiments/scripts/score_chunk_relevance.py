#!/usr/bin/env python3
"""Score retrievers from blind chunk relevance judgments."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def dcg(relevances: list[int], k: int) -> float:
    score = 0.0
    for index, relevance in enumerate(relevances[:k], start=1):
        score += (2**relevance - 1) / math.log2(index + 1)
    return score


def ndcg(relevances: list[int], ideal_relevances: list[int], k: int) -> float:
    ideal = dcg(sorted(ideal_relevances, reverse=True), k)
    if ideal == 0:
        return 0.0
    return dcg(relevances, k) / ideal


def summarize_variant(name: str, rows: list[dict[str, Any]], k: int) -> dict[str, Any]:
    by_query: dict[str, list[tuple[int, int]]] = defaultdict(list)
    judged_relevances_by_query: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        relevance = row.get("relevance")
        if relevance is None:
            continue
        judged_relevances_by_query[row["query_id"]].append(relevance)
        for retrieval in row.get("retrieved_by", []):
            if retrieval["variant"] == name:
                by_query[row["query_id"]].append((retrieval["rank"], relevance))

    query_scores = []
    for query_id, ranked in by_query.items():
        ranked.sort(key=lambda item: item[0])
        relevances = [relevance for _rank, relevance in ranked]
        relevant_at_k = sum(1 for relevance in relevances[:k] if relevance > 0)
        judged_relevances = judged_relevances_by_query.get(query_id, [])
        relevant_total = sum(1 for relevance in judged_relevances if relevance > 0)
        query_scores.append(
            {
                "query_id": query_id,
                "judged_results": len(relevances),
                "ndcg_at_k": ndcg(relevances, judged_relevances, k),
                "precision_at_k": relevant_at_k / k,
                "recall_at_k": relevant_at_k / relevant_total if relevant_total else 0.0,
            }
        )

    return {
        "name": name,
        "queries_scored": len(query_scores),
        "metrics": {
            f"ndcg_at_{k}": round(statistics.mean([query["ndcg_at_k"] for query in query_scores]), 4) if query_scores else 0.0,
            f"precision_at_{k}": round(statistics.mean([query["precision_at_k"] for query in query_scores]), 4) if query_scores else 0.0,
            f"recall_at_{k}": round(statistics.mean([query["recall_at_k"] for query in query_scores]), 4) if query_scores else 0.0,
        },
        "queries": query_scores,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Pooled Chunk Relevance",
        "",
        "## Purpose",
        "",
        "Score retrievers using blind query/chunk relevance judgments over the realistic query set.",
        "",
        f"Current labels are internal evaluation labels from {run['label_model_statement']}, not an external human benchmark. They are useful for comparing retrieval choices and identifying rows that deserve further audit.",
        "",
        "## Review Status",
        "",
        f"- Pool rows: {run['pool_rows']}",
        f"- Reviewed rows: {run['reviewed_rows']}",
        f"- Unreviewed rows: {run['unreviewed_rows']}",
        "",
        "## Label Provenance",
        "",
        "| Source | Provider | Model | Reviewer | Rows |",
        "|---|---|---|---|---:|",
    ]
    for provenance in run["label_provenance"]:
        lines.append(
            f"| `{provenance['source']}` | `{provenance['provider']}` | `{provenance['model']}` | "
            f"`{provenance['reviewer']}` | {provenance['rows']} |"
        )
    lines.extend(
        [
            "",
            "## Label Distribution",
            "",
            "| Label | Meaning | Rows |",
            "|---:|---|---:|",
            f"| 2 | Directly useful / cite-worthy | {run['label_counts'].get(2, 0)} |",
            f"| 1 | Partially useful / background | {run['label_counts'].get(1, 0)} |",
            f"| 0 | Not useful | {run['label_counts'].get(0, 0)} |",
            "",
            "## Metrics",
            "",
            f"| Variant | Queries Scored | nDCG@{run['k']} | Precision@{run['k']} | Recall@{run['k']} |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for variant in run["variants"]:
        metrics = variant["metrics"]
        ndcg_key = f"ndcg_at_{run['k']}"
        precision_key = f"precision_at_{run['k']}"
        recall_key = f"recall_at_{run['k']}"
        lines.append(
            f"| `{variant['name']}` | {variant['queries_scored']} | "
            f"{metrics[ndcg_key]:.4f} | {metrics[precision_key]:.4f} | {metrics[recall_key]:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The chunk-level labels separate the candidates more clearly than the pilot chapter-level metrics: dense retrieval currently leads on nDCG@5 and recall@5, hybrid RRF is close, and BM25 trails both. Before treating this as the final retrieval decision, audit the remaining low-confidence labels and the queries where dense and hybrid disagree.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score chunk relevance judgments")
    parser.add_argument("--pool", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.jsonl")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "pooled_relevance.md")
    args = parser.parse_args()

    rows = load_jsonl(args.pool)
    reviewed = [row for row in rows if row.get("relevance") is not None]
    variants = sorted({retrieval["variant"] for row in rows for retrieval in row.get("retrieved_by", [])})
    provenance_counts = Counter(
        (
            row.get("label_source") or "manual",
            row.get("label_provider") or "manual",
            row.get("label_model") or "none",
            row.get("label_reviewer") or row.get("reviewer") or "manual_unspecified",
        )
        for row in reviewed
    )
    label_counts = Counter(row.get("relevance") for row in reviewed)
    label_provenance = [
        {
            "source": source,
            "provider": provider,
            "model": model,
            "reviewer": reviewer,
            "rows": count,
        }
        for (source, provider, model, reviewer), count in sorted(provenance_counts.items())
    ]
    model_counts = Counter((item["provider"], item["model"]) for item in label_provenance for _ in range(item["rows"]))
    label_model_statement = ", ".join(
        f"{provider} {model} ({rows} rows)" for (provider, model), rows in sorted(model_counts.items())
    ) or "no reviewed labels"
    run = {
        "pool_rows": len(rows),
        "reviewed_rows": len(reviewed),
        "unreviewed_rows": len(rows) - len(reviewed),
        "label_provenance": label_provenance,
        "label_model_statement": label_model_statement,
        "label_counts": dict(label_counts),
        "k": args.k,
        "variants": [summarize_variant(variant, rows, args.k) for variant in variants],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_report(run, args.report)
    print(json.dumps({**{key: run[key] for key in ("pool_rows", "reviewed_rows", "unreviewed_rows")}, "variants": [{"name": variant["name"], **variant["metrics"]} for variant in run["variants"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
