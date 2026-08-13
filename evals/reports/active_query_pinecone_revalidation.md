# Active-Query Pinecone Revalidation

> Superseded for the active runtime by
> `pinecone_large_embedding_revalidation.md`. This report preserves the namespace
> comparison performed with `text-embedding-3-small`.

## Method

Framework-aware chunks were indexed in one Pinecone namespace and in five subject namespaces. All 46 cases used the same frozen `gpt-5.5` corpus-guided query, unfiltered hybrid retrieval, cached embeddings, and top-five cutoff. Requests ran sequentially to measure one product request at a time.

The subject condition used answer-key subjects. It is an optimistic infrastructure comparison, not a runtime policy the product can execute without adding and testing a semantic router.

## Results

| Layout | Hit@1 | Hit@3 | Hit@5 | Mean rank | Useful@5 | Noise@5 | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| One namespace | 93.5% | 97.8% | 100.0% | 1.152 | 78.7% | 21.3% | 4.07s | 7.64s |
| Oracle subject namespaces | 93.5% | 97.8% | 100.0% | 1.130 | 78.7% | 21.3% | 2.28s | 10.47s |

The exact top-five ordering matched in 37 of 46 cases. The subject split did not improve any hit-rate cutoff or Useful@5, and it worsened tail latency.

The saved Pinecone retrieval lists were rescored after the framework-boundary label
audit. Retrieval and latency were not rerun. The machine-readable files below preserve
the original retrieval run and its pre-audit useful-count fields.

## Decision

Use one unfiltered namespace. The oracle layout does not justify a new subject-routing dependency, and hosted latency still needs optimization before production-readiness claims.

Machine-readable outputs:

- `evals/reports/active_query_pinecone_revalidation_summary.json`
- `evals/reports/active_query_pinecone_revalidation_cases.jsonl`
