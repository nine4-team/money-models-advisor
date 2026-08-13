# Embedding Model Comparison

## Decision Rule

Adopt `text-embedding-3-large` at the deployable 1,536 dimensions only if it preserves Hit@5 and improves Useful@5 by at least 2 percentage points or mean first-useful rank by at least 0.10. Otherwise retain the cheaper `text-embedding-3-small`.

## Method

Both models use the same 46 frozen corpus-guided queries, framework-aware chunks, local hybrid retrieval, top-five cutoff, and audited relevance labels. API calls create only deterministic embeddings; no external model generates queries or judgments.

The larger model introduced 39 case-passage pairs not returned by the small-model top five. All were reviewed before the decision; the audit added 6 missed useful labels and removed 0 overly broad labels.

## Results

| Model | Hit@1 | Hit@3 | Hit@5 | Mean rank | Useful@5 | Noise@5 | Query p50 | Query p95 | Est. uncached cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `text-embedding-3-small` | 93.5% | 97.8% | 100.0% | 1.152 | 78.7% | 21.3% | 0.03s | 0.03s | $0.002657 |
| `text-embedding-3-large-d1536` | 93.5% | 97.8% | 100.0% | 1.109 | 86.5% | 13.5% | 0.03s | 0.03s | $0.017274 |

## Decision

Use `text-embedding-3-large-d1536`. The larger model is adopted only if it clears the rule above.

Machine-readable outputs:

- `evals/reports/embedding_model_comparison_summary.json`
- `evals/reports/embedding_model_comparison_cases.jsonl`
