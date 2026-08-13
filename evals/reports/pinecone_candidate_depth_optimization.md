# Pinecone Candidate-Depth Optimization

This experiment used `text-embedding-3-small`. The candidate-depth correction remains
in the runtime; the selected large-model hosted replay is recorded in
`pinecone_large_embedding_revalidation.md`.

## Question

Can the active one-query Pinecone path reduce latency without changing the top-five
results used by the advisor?

## Change

Hybrid retrieval needs 25 candidates from each ranker to produce five fused results.
The vector adapter was multiplying that candidate count by ten again, so Pinecone was
asked for 250 vectors from a 204-chunk index. The extra 225 results were discarded
before rank fusion.

The runtime now requests the 25 candidates that hybrid retrieval actually consumes.
The 46 frozen `gpt-5.5` corpus-guided queries were then replayed sequentially against
the same framework-aware Pinecone namespace.

## Results

| Run | Vector candidates requested | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Before | 250 | 93.5% | 97.8% | 100.0% | 78.7% | 21.3% | 4.07s | 7.64s |
| After | 25 | 93.5% | 97.8% | 100.0% | 78.7% | 21.3% | 0.89s | 1.14s |

All 46 top-five lists matched the earlier run exactly. One request in the new run
took 6.29s; the remaining tail stayed low enough for a 1.14s p95.

## Decision

Keep the 25-candidate hybrid depth and remove the redundant vector over-fetch. It
preserves the active ranking while reducing returned payload and observed latency.

Machine-readable outputs:

- `evals/reports/pinecone_candidate_depth_optimization_summary.json`
- `evals/reports/pinecone_candidate_depth_optimization_cases.jsonl`
