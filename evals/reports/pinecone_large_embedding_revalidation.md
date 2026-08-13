# Pinecone Revalidation — Selected Large Embedding

## Method

The 204 framework-aware chunks were embedded with `text-embedding-3-large` at
1,536 dimensions and written to the isolated
`money-models-framework-large-d1536` namespace. All 46 frozen corpus-guided queries
then ran sequentially through the active one-query hybrid path with 25 lexical and 25
vector candidates fused to five results.

## Results

| Hit@1 | Hit@3 | Hit@5 | Mean rank | Useful@5 | Noise@5 | p50 | p95 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 93.5% | 97.8% | 100.0% | 1.109 | 86.1% | 13.9% | 1.13s | 1.43s |

The hosted top-five order matched the local selected-model run in 44 of 46 cases.
One difference was only an order swap; the other replaced one useful fifth result
with a general attraction passage that the semantic audit had already labeled not
useful. Hit-rate cutoffs were unchanged.

## Decision

Use `text-embedding-3-large` at 1,536 dimensions in the isolated Pinecone namespace.
The hosted replay preserves 100% Hit@5 and most of the local Useful@5 improvement while
remaining within the optimized request-latency range.

Machine-readable outputs:

- `evals/reports/pinecone_large_embedding_revalidation_summary.json`
- `evals/reports/pinecone_large_embedding_revalidation_cases.jsonl`
