# Evaluation Reports

This directory holds experiment reports that justify architecture choices with measured comparisons.

Each report should use this structure:

```text
# Experiment Name

## Hypothesis

## Variants

## Dataset Slice

## Metrics

## Results

## Decision

## Failure Analysis

## Next Experiment
```

Recommended metrics:

- `router_accuracy`
- `hit@1`
- `hit@5`
- `mrr`
- `ndcg@10`
- `faithfulness`
- `structured_output_validity`
- `p50_latency_ms`
- `p95_latency_ms`
- `cost_per_query_usd`
- `api_tokens`
- `cache_hits`
- `required_claim_support_coverage`

The goal is to make RAG architecture decisions the way an ML workflow makes model or hyperparameter decisions: by comparing variants under the same dataset, metrics, and adoption threshold.

Cost notes should distinguish first-run spend from warm-cache reruns. Embedding experiments use deterministic embeddings, so reports should include `api_tokens` and `cache_hits` when applicable. The local OpenAI embedding client stores cached vectors in `.cache/embeddings.sqlite3`, keyed by model and text hash.

The active retrieval-support guardrail is required-claim support coverage. Required supported claims live in `evals/obligations.jsonl`; review them with `PYTHONPATH=src python3 scripts/review_obligations.py`, then score accepted labels with `PYTHONPATH=src python3 scripts/score_obligation_support.py`. Use `--include-proposed` only when a future label batch has unreviewed proposed rows.

Use `PYTHONPATH=src python3 scripts/retrieval_required_claim_ablation.py` to compare BM25, dense-only, hybrid RRF, and lexical-anchor hybrid against the accepted required-claim labels. This report is the main evidence-support guardrail for retrieval variants.

For final retriever selection, use realistic queries and blind chunk relevance judgments:

```bash
PYTHONPATH=src python3 scripts/audit_query_realism.py
PYTHONPATH=src python3 scripts/build_chunk_relevance_pool.py
PYTHONPATH=src python3 scripts/review_chunk_relevance.py --port 8766
PYTHONPATH=src python3 scripts/score_chunk_relevance.py
```

Old keyword evidence-term experiments are archived under `archive/keyword-evidence-proxy/` and are not part of the active design.
