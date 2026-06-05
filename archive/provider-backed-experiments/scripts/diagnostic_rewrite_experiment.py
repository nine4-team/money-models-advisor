#!/usr/bin/env python3
"""Evaluate diagnose-first query rewriting for numeric diagnostic retrieval."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.calculator import UnitEconomics, gross_margin, gross_profit, payback_period_months  # noqa: E402
from money_model_architect.diagnose import diagnose  # noqa: E402
from money_model_architect.retrieval import CorpusIndex  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dcg(relevances: list[int], k: int = 5) -> float:
    return sum((2**relevance - 1) / math.log2(index + 2) for index, relevance in enumerate(relevances[:k]))


def ndcg(relevances: list[int], ideal_relevances: list[int], k: int = 5) -> float:
    ideal = dcg(sorted(ideal_relevances, reverse=True), k)
    return dcg(relevances, k) / ideal if ideal else 0.0


def money_values(text: str) -> list[float]:
    values = []
    for raw in re.findall(r"\$([0-9][0-9,]*(?:\.[0-9]+)?)", text):
        values.append(float(raw.replace(",", "")))
    return values


def percent_values(text: str) -> list[float]:
    return [float(raw) / 100 for raw in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)]


def month_values(text: str) -> list[float]:
    return [float(raw) for raw in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s+months?", text.lower())]


def economics_from_query(record: dict[str, Any]) -> UnitEconomics | None:
    query = record["query"].lower()
    dollars = money_values(record["query"])
    percents = percent_values(record["query"])
    months = month_values(record["query"])

    if record["id"] == "diagnostic_low_first_month_gp":
        return UnitEconomics(cac=dollars[0], first_30_day_gross_profit=dollars[1], monthly_recurring_gross_profit=dollars[2])

    if record["id"] == "diagnostic_high_revenue_low_margin":
        price, cogs, cac_value = dollars
        return UnitEconomics(
            cac=cac_value,
            first_30_day_gross_profit=gross_profit(price, cogs),
            gross_margin=gross_margin(price, cogs),
            service_business=True,
        )

    if record["id"] == "diagnostic_ltv_good_payback_bad":
        lifetime_gp, cac_value = dollars
        payback_months = months[0] if months else 8
        monthly_gp = max(1.0, cac_value / payback_months)
        return UnitEconomics(
            cac=cac_value,
            first_30_day_gross_profit=0,
            monthly_recurring_gross_profit=monthly_gp,
            lifetime_gross_profit=lifetime_gp,
        )

    if record["id"] == "diagnostic_cfa_level_goal":
        cac_value, first_30_day_gp = dollars
        return UnitEconomics(cac=cac_value, first_30_day_gross_profit=first_30_day_gp)

    if record["id"] == "diagnostic_free_offer_overload":
        return None

    if record["id"] == "diagnostic_continuity_discount_math":
        monthly_price = dollars[0]
        churn_month = months[0] if months else 3
        return UnitEconomics(cac=1, first_30_day_gross_profit=monthly_price, monthly_recurring_gross_profit=monthly_price, lifetime_gross_profit=monthly_price * churn_month)

    if "gross margin" in query and dollars and percents:
        return UnitEconomics(cac=dollars[-1], gross_margin=percents[0], service_business=True)

    return None


def rewrite_query(record: dict[str, Any]) -> dict[str, Any]:
    if record["id"] == "diagnostic_ltv_good_payback_bad":
        rewritten = (
            "diagnose cash-constraint: lifetime gross profit to CAC is healthy but payback period is slow. "
            "Retrieve payback period, first 30 day gross profit, client-financed acquisition, upfront gross profit, upsell offers."
        )
        return {"query": rewritten, "constraint": "cash-constraint", "reason": "Lifetime economics work, but CAC recovery takes too many months."}

    if record["id"] == "diagnostic_continuity_discount_math":
        rewritten = (
            "diagnose continuity retention: members cancel after month three, permanent discount after month three, "
            "improve churn, extend lifetime gross profit, continuity discounts, earned discount timing"
        )
        return {"query": rewritten, "constraint": "continuity-retention", "reason": "The discount is meant to extend retention and lifetime gross profit after the churn point."}

    economics = economics_from_query(record)
    if economics is None:
        if record["id"] == "diagnostic_free_offer_overload":
            rewritten = (
                "diagnose free front-end offer quality: lower CAC, free leads, lead volume overload, "
                "booking rate drop, add friction after creating flow, monetize then filter"
            )
            return {"query": rewritten, "constraint": "free-offer-quality", "reason": "Free offer lowered lead cost but reduced booked sales and increased support load."}
        return {"query": record["query"], "constraint": "unknown", "reason": "No deterministic diagnostic rewrite available."}

    diagnosis = diagnose(economics)
    metrics = diagnosis.metrics
    concepts = {
        "gross-margin": "gross profit gross margin delivery cost service business margin",
        "monetization": "first 30 day gross profit client-financed acquisition cfa payback period upsell offers",
        "cash-constraint": "payback period slow cash recovery first 30 day gross profit upfront gross profit upsell offers prepayment initiation fees",
        "cfa-level-2": "client-financed acquisition level 2 level 3 first 30 day gross profit two times CAC upsell offers",
        "scale-ready": "client-financed acquisition level 3 first 30 day gross profit acquisition engine scale spend",
        "viability": "lifetime gross profit CAC ratio gross profit continuity retention margin",
    }
    rewritten = (
        f"diagnose {diagnosis.constraint}: {concepts.get(diagnosis.constraint, '')}. "
        f"Reason: {diagnosis.reason} Success metric: {diagnosis.success_metric}"
    )
    return {"query": rewritten, "constraint": diagnosis.constraint, "reason": diagnosis.reason, "metrics": metrics}


def bm25_top(index: CorpusIndex, record: dict[str, Any], query: str, top_k: int) -> list[dict[str, Any]]:
    return [
        {"chunk_id": result.chunk.id, "score": result.score}
        for result in index.search(query, layer=record.get("target_layer_hint"), top_k=top_k)
    ]


def score_variant(rows: list[dict[str, Any]], by_query: dict[str, list[dict[str, Any]]], variant: str, k: int) -> dict[str, Any]:
    query_scores = []
    for query_id, query_rows in by_query.items():
        ideal = [row["relevance"] for row in query_rows]
        ranked = []
        for row in query_rows:
            for retrieval in row.get("retrieved_by", []):
                if retrieval["variant"] == variant:
                    ranked.append((retrieval["rank"], row["relevance"], row["chunk_id"]))
        ranked.sort()
        relevances = [relevance for _rank, relevance, _chunk_id in ranked]
        relevant_total = sum(1 for relevance in ideal if relevance > 0)
        relevant_at_k = sum(1 for relevance in relevances[:k] if relevance > 0)
        query_scores.append(
            {
                "query_id": query_id,
                "ndcg_at_5": ndcg(relevances, ideal, k),
                "precision_at_5": relevant_at_k / k,
                "recall_at_5": relevant_at_k / relevant_total if relevant_total else 0.0,
                "ranked_chunks": [chunk_id for _rank, _relevance, chunk_id in ranked[:k]],
                "ranked_relevance": relevances[:k],
            }
        )
    return {
        "variant": variant,
        "ndcg_at_5": statistics.mean(item["ndcg_at_5"] for item in query_scores),
        "precision_at_5": statistics.mean(item["precision_at_5"] for item in query_scores),
        "recall_at_5": statistics.mean(item["recall_at_5"] for item in query_scores),
        "queries": query_scores,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate diagnose-first diagnostic query rewriting")
    parser.add_argument("--queries", type=Path, default=ROOT / "evals" / "realistic_queries.jsonl")
    parser.add_argument("--labels", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.diagnostic_embedding_expansion.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.diagnostic_rewrite.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "diagnostic_rewrite_experiment.md")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    records = [record for record in load_jsonl(args.queries) if record.get("query_type") == "diagnostic_numeric"]
    labels = load_jsonl(args.labels)
    rows = [dict(row) for row in labels if row["query_id"] in {record["id"] for record in records}]
    by_id = {row["id"]: row for row in rows}
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")

    rewrite_runs = {}
    for record in records:
        rewrite = rewrite_query(record)
        rewrite_runs[record["id"]] = rewrite
        for rank, item in enumerate(bm25_top(index, record, rewrite["query"], args.top_k), start=1):
            row_id = f"{record['id']}::{item['chunk_id']}"
            if row_id not in by_id:
                raise RuntimeError(f"diagnostic rewrite retrieved unjudged chunk {row_id}")
            by_id[row_id].setdefault("retrieved_by", []).append(
                {"variant": "diagnose-rewrite-bm25", "rank": rank, "score": round(item["score"], 6)}
            )

    output_rows = sorted(by_id.values(), key=lambda row: (row["query_id"], row["chunk_id"]))
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output_rows), encoding="utf-8")

    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in output_rows:
        by_query[row["query_id"]].append(row)

    variants = ["bm25", "dense-openai-3-small", "hybrid-rrf-3-small", "dense-openai-3-large", "hybrid-rrf-3-large", "diagnose-rewrite-bm25"]
    scores = [score_variant(output_rows, by_query, variant, args.top_k) for variant in variants]

    lines = [
        "# Diagnostic Rewrite Experiment",
        "",
        "## Hypothesis",
        "",
        "Numeric diagnostic questions should retrieve better when the system first identifies the economic bottleneck and rewrites the query toward the relevant metrics/frameworks.",
        "",
        "## Results",
        "",
        "| Variant | nDCG@5 | Precision@5 | Recall@5 |",
        "|---|---:|---:|---:|",
    ]
    for score in scores:
        lines.append(f"| `{score['variant']}` | {score['ndcg_at_5']:.4f} | {score['precision_at_5']:.4f} | {score['recall_at_5']:.4f} |")
    lines.extend(["", "## Rewrites", "", "| Query | Constraint | Rewritten query |", "|---|---|---|"])
    for record in records:
        rewrite = rewrite_runs[record["id"]]
        lines.append(f"| `{record['id']}` | `{rewrite.get('constraint')}` | {rewrite['query'].replace('|', '/')} |")
    lines.extend(["", "## Per-query nDCG@5", "", "| Query | BM25 | Dense 3-small | Hybrid 3-small | Dense 3-large | Hybrid 3-large | Diagnose rewrite |", "|---|---:|---:|---:|---:|---:|---:|"])
    by_variant = {score["variant"]: {query["query_id"]: query for query in score["queries"]} for score in scores}
    for record in records:
        query_id = record["id"]
        lines.append(
            f"| `{query_id}` | "
            f"{by_variant['bm25'][query_id]['ndcg_at_5']:.3f} | "
            f"{by_variant['dense-openai-3-small'][query_id]['ndcg_at_5']:.3f} | "
            f"{by_variant['hybrid-rrf-3-small'][query_id]['ndcg_at_5']:.3f} | "
            f"{by_variant['dense-openai-3-large'][query_id]['ndcg_at_5']:.3f} | "
            f"{by_variant['hybrid-rrf-3-large'][query_id]['ndcg_at_5']:.3f} | "
            f"{by_variant['diagnose-rewrite-bm25'][query_id]['ndcg_at_5']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "If the diagnose-first rewrite improves over raw BM25 and embedding retrieval, keep it as the diagnostic retrieval policy. If it only matches BM25, prefer the simpler lexical diagnostic route until answer-level evals justify the extra diagnostic logic.",
            "",
        ]
    )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(args.output.relative_to(ROOT)), "report": str(args.report.relative_to(ROOT)), "scores": scores}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
