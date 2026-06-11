# Retrieval Backend Comparison

## Scope

This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.

- Query source: `generated_variants`
- Top K: `5`
- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.
- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.

Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.

## Metrics

| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |
|---|---:|---:|---:|---:|---:|---:|---|
| `bm25` | 30 | 96.7% | 100.0% | 100.0% | 100.0% | 1.3 | none |
| `vector` | 30 | 96.7% | 100.0% | 100.0% | 100.0% | 1.37 | none |
| `hybrid` | 30 | 100.0% | 100.0% | 100.0% | 100.0% | 1.17 | none |

## Performance And Cost

| Backend | p50 Total | p95 Total | p50 Retrieval | p95 Retrieval | p50 Embedding | p95 Embedding | Avg Queries | Avg Variants | Vector Searches | Query Cache Hit Rate | Corpus Cache Hit Rate | API Batches | Estimated Cost | Est. Cost / 1K Queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `bm25` | 0.948 ms | 3.703 ms | 0.8 ms | 2.995 ms | 0.0 ms | 0.0 ms | 4.0 | 3.0 | 0 | n/a | n/a | 0 | $0.00000000 | $0.00000000 |
| `vector` | 41.559 ms | 108.537 ms | 41.349 ms | 108.302 ms | 3.023 ms | 3.544 ms | 4.0 | 3.0 | 120 | 100.0% | 100.0% | 0 | $0.00000000 | $0.00000000 |
| `hybrid` | 40.63 ms | 110.338 ms | 40.401 ms | 110.124 ms | 2.121 ms | 2.342 ms | 4.0 | 3.0 | 120 | 100.0% | 100.0% | 0 | $0.00000000 | $0.00000000 |

## Cache State

- `vector`: cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.
- `hybrid`: cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.

## Dataset

- Scored cases: 30

## Interpretation

- Best eval-slice result by Hit@5 and mean known-useful rank: `hybrid` at 100.0% Hit@5 and mean rank 1.17.
- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive.
- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite.
