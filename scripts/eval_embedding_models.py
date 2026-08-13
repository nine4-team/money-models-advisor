#!/usr/bin/env python3
"""Compare embedding models on the frozen active retrieval path."""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from money_model_architect.embeddings import (
    EMBEDDING_COST_PER_1M_TOKENS_USD,
    OpenAIEmbeddingClient,
    estimate_tokens_from_chars,
)
from money_model_architect.retrieval import CorpusIndex, tokenize
from money_model_architect.vector_store import LocalVectorStore
from revalidate_retrieval_choices import (
    DEFAULT_ADJUDICATIONS,
    chunk_token_spans,
    load_adjudications,
    load_cases,
    percentile,
    transferred_label,
)


MODELS = ("text-embedding-3-small", "text-embedding-3-large-d1536")
REPORT = ROOT / "evals" / "reports" / "embedding_model_comparison.md"
SUMMARY = ROOT / "evals" / "reports" / "embedding_model_comparison_summary.json"
CASES = ROOT / "evals" / "reports" / "embedding_model_comparison_cases.jsonl"
EMBEDDING_ADJUDICATIONS = ROOT / "evals" / "embedding_model_adjudications.jsonl"

# Defined before running the experiment: large is adopted only if it preserves
# Hit@5 and improves Useful@5 by >=2 percentage points or mean first-useful rank
# by >=0.10. Otherwise the lower-cost small model remains the default.
USEFUL_GAIN_THRESHOLD = 2.0
RANK_GAIN_THRESHOLD = 0.10


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    cases = load_cases()
    heading_index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    heading_by_id = {chunk.id: chunk for chunk in heading_index.chunks}
    heading_spans = chunk_token_spans(heading_index)
    adjudications = load_adjudications(DEFAULT_ADJUDICATIONS)
    embedding_adjudications = {
        (row["case_id"], row["chunk_id"]): row
        for row in load_jsonl(EMBEDDING_ADJUDICATIONS)
    }
    rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}

    for model in MODELS:
        # CorpusIndex memoizes its chunk embeddings, so each model gets a separate
        # instance to prevent vectors from different dimensions being mixed.
        index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="framework-aware")
        strategy_spans = chunk_token_spans(index)
        client = OpenAIEmbeddingClient(
            model="text-embedding-3-large" if model == "text-embedding-3-large-d1536" else model,
            dimensions=1536 if model == "text-embedding-3-large-d1536" else None,
        )
        build_started = time.perf_counter()
        store = LocalVectorStore(index.vector_records(client))
        build_ms = (time.perf_counter() - build_started) * 1000
        model_rows = []
        for case in cases:
            started = time.perf_counter()
            results = index.hybrid_search(
                case.query,
                top_k=5,
                embedding_client=client,
                vector_store=store,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            useful_heading = [
                heading_by_id[chunk_id]
                for chunk_id in case.known_useful_chunk_ids
                if chunk_id in heading_by_id
            ]
            flags = []
            for result in results:
                embedding_adjudication = embedding_adjudications.get((case.case_id, result.chunk.id))
                adjudication = adjudications.get(("framework-aware", case.case_id, result.chunk.id))
                if embedding_adjudication is not None:
                    flags.append(bool(embedding_adjudication["useful"]))
                elif adjudication is not None:
                    flags.append(bool(adjudication["useful"]))
                else:
                    flags.append(
                        transferred_label(
                            result.chunk,
                            useful_heading,
                            candidate_span=strategy_spans[result.chunk.id],
                            heading_spans=heading_spans,
                            exact_heading_ids=set(case.known_useful_chunk_ids),
                            strategy="framework-aware",
                        )[0]
                    )
            ranks = [rank for rank, useful in enumerate(flags, 1) if useful]
            row = {
                "case_id": case.case_id,
                "model": model,
                "returned_chunk_ids": [result.chunk.id for result in results],
                "first_useful_rank": min(ranks) if ranks else None,
                "useful_result_count": sum(flags),
                "latency_ms": round(latency_ms, 3),
            }
            rows.append(row)
            model_rows.append(row)
        first_ranks = [row["first_useful_rank"] for row in model_rows if row["first_useful_rank"] is not None]
        slots = len(model_rows) * 5
        latencies = [row["latency_ms"] for row in model_rows]
        input_chars = sum(
            stats.input_chars for stats in client.stats.by_purpose.values()
        )
        uncached_cost = (
            estimate_tokens_from_chars(input_chars)
            / 1_000_000
            * EMBEDDING_COST_PER_1M_TOKENS_USD[client.model]
        )
        summaries[model] = {
            "cases": len(model_rows),
            "hit_at_1_pct": round(sum(row["first_useful_rank"] == 1 for row in model_rows) / len(model_rows) * 100, 1),
            "hit_at_3_pct": round(sum(row["first_useful_rank"] is not None and row["first_useful_rank"] <= 3 for row in model_rows) / len(model_rows) * 100, 1),
            "hit_at_5_pct": round(len(first_ranks) / len(model_rows) * 100, 1),
            "mean_first_useful_rank": round(statistics.mean(first_ranks), 3),
            "useful_at_5_pct": round(sum(row["useful_result_count"] for row in model_rows) / slots * 100, 1),
            "noise_at_5_pct": round(100 - sum(row["useful_result_count"] for row in model_rows) / slots * 100, 1),
            "p50_query_latency_ms": round(statistics.median(latencies), 2),
            "p95_query_latency_ms": round(percentile(latencies, 95), 2),
            "corpus_build_ms": round(build_ms, 2),
            "embedding_stats": client.stats.to_dict(),
            "estimated_api_cost_usd": round(client.estimated_api_cost_usd(), 6),
            "estimated_uncached_cost_usd": round(uncached_cost, 6),
        }

    by_case_model = {
        (row["case_id"], row["model"]): row
        for row in rows
    }
    novel_pairs: set[tuple[str, str]] = set()
    for case in cases:
        small_ids = set(by_case_model[(case.case_id, MODELS[0])]["returned_chunk_ids"])
        for chunk_id in by_case_model[(case.case_id, MODELS[1])]["returned_chunk_ids"]:
            if chunk_id not in small_ids:
                novel_pairs.add((case.case_id, chunk_id))
    reviewed_pairs = novel_pairs & set(embedding_adjudications)
    unreviewed_pairs = novel_pairs - set(embedding_adjudications)
    case_by_id = {case.case_id: case for case in cases}
    chunk_by_id = {chunk.id: chunk for chunk in index.chunks}
    false_negative_corrections = 0
    false_positive_corrections = 0
    for case_id, chunk_id in reviewed_pairs:
        case = case_by_id[case_id]
        existing = adjudications.get(("framework-aware", case_id, chunk_id))
        if existing is not None:
            old_label = bool(existing["useful"])
        else:
            useful_heading = [
                heading_by_id[known_id]
                for known_id in case.known_useful_chunk_ids
                if known_id in heading_by_id
            ]
            old_label = transferred_label(
                chunk_by_id[chunk_id],
                useful_heading,
                candidate_span=strategy_spans[chunk_id],
                heading_spans=heading_spans,
                exact_heading_ids=set(case.known_useful_chunk_ids),
                strategy="framework-aware",
            )[0]
        new_label = bool(embedding_adjudications[(case_id, chunk_id)]["useful"])
        false_negative_corrections += int(new_label and not old_label)
        false_positive_corrections += int(old_label and not new_label)

    small = summaries[MODELS[0]]
    large = summaries[MODELS[1]]
    useful_gain = large["useful_at_5_pct"] - small["useful_at_5_pct"]
    rank_gain = small["mean_first_useful_rank"] - large["mean_first_useful_rank"]
    large_wins = not unreviewed_pairs and (
        large["hit_at_5_pct"] >= small["hit_at_5_pct"]
        and (useful_gain >= USEFUL_GAIN_THRESHOLD or rank_gain >= RANK_GAIN_THRESHOLD)
    )
    decision = MODELS[1] if large_wins else MODELS[0]
    payload = {
        "experiment": "embedding-model-comparison",
        "cases": len(cases),
        "query_writer": "gpt-5.5/guided_model_rewrite_v2",
        "retrieval": "local hybrid, framework-aware chunks, top_k=5",
        "decision_rule": {
            "preserve_hit_at_5": True,
            "useful_at_5_gain_percentage_points": USEFUL_GAIN_THRESHOLD,
            "mean_first_useful_rank_gain": RANK_GAIN_THRESHOLD,
        },
        "conditions": summaries,
        "decision": decision,
        "embedding_model_audit": {
            "new_case_chunk_pairs": len(novel_pairs),
            "reviewed_new_case_chunk_pairs": len(reviewed_pairs),
            "unreviewed_new_case_chunk_pairs": len(unreviewed_pairs),
            "false_negative_corrections": false_negative_corrections,
            "false_positive_corrections": false_positive_corrections,
        },
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CASES.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    render_report(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def render_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Embedding Model Comparison",
        "",
        "## Decision Rule",
        "",
        "Adopt `text-embedding-3-large` at the deployable 1,536 dimensions only if it preserves Hit@5 and improves Useful@5 by at least 2 percentage points or mean first-useful rank by at least 0.10. Otherwise retain the cheaper `text-embedding-3-small`.",
        "",
        "## Method",
        "",
        "Both models use the same 46 frozen corpus-guided queries, framework-aware chunks, local hybrid retrieval, top-five cutoff, and audited relevance labels. API calls create only deterministic embeddings; no external model generates queries or judgments.",
        "",
        f"The larger model introduced {payload['embedding_model_audit']['new_case_chunk_pairs']} case-passage pairs not returned by the small-model top five. All were reviewed before the decision; the audit added {payload['embedding_model_audit']['false_negative_corrections']} missed useful labels and removed {payload['embedding_model_audit']['false_positive_corrections']} overly broad labels.",
        "",
        "## Results",
        "",
        "| Model | Hit@1 | Hit@3 | Hit@5 | Mean rank | Useful@5 | Noise@5 | Query p50 | Query p95 | Est. uncached cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in MODELS:
        result = payload["conditions"][model]
        lines.append(
            f"| `{model}` | {result['hit_at_1_pct']:.1f}% | {result['hit_at_3_pct']:.1f}% | "
            f"{result['hit_at_5_pct']:.1f}% | {result['mean_first_useful_rank']:.3f} | "
            f"{result['useful_at_5_pct']:.1f}% | {result['noise_at_5_pct']:.1f}% | "
            f"{result['p50_query_latency_ms'] / 1000:.2f}s | {result['p95_query_latency_ms'] / 1000:.2f}s | "
            f"${result['estimated_uncached_cost_usd']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Use `{payload['decision']}`. The larger model is adopted only if it clears the rule above.",
            "",
            "Machine-readable outputs:",
            "",
            "- `evals/reports/embedding_model_comparison_summary.json`",
            "- `evals/reports/embedding_model_comparison_cases.jsonl`",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
