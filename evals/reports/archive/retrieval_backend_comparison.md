# Retrieval Backend Comparison

## Scope

This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.

- Query source: `generated`
- Top K: `5`
- Vector store: `local`
- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.
- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.

Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.

## Metrics

| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |
|---|---:|---:|---:|---:|---:|---:|---|
| `bm25` | 30 | 93.3% | 100.0% | 100.0% | 100.0% | 1.43 | none |
| `vector` | 30 | 96.7% | 96.7% | 100.0% | 100.0% | 1.34 | `searchq_v1_001` |
| `hybrid` | 30 | 96.7% | 96.7% | 100.0% | 100.0% | 1.21 | `searchq_v1_001` |

## Performance And Cost

| Backend | p50 Total | p95 Total | p50 Retrieval | p95 Retrieval | p50 Embedding | p95 Embedding | Avg Queries | Avg Variants | Vector Searches | Query Cache Hit Rate | Corpus Cache Hit Rate | API Batches | Estimated Cost | Est. Cost / 1K Queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `bm25` | 0.272 ms | 0.672 ms | 0.204 ms | 0.602 ms | 0.0 ms | 0.0 ms | 1.0 | 0.0 | 0 | n/a | n/a | 0 | $0.00000000 | $0.00000000 |
| `vector` | 11.019 ms | 33.636 ms | 10.879 ms | 33.424 ms | 0.734 ms | 1.719 ms | 1.0 | 0.0 | 30 | 100.0% | 100.0% | 0 | $0.00000000 | $0.00000000 |
| `hybrid` | 10.81 ms | 28.14 ms | 10.705 ms | 28.028 ms | 0.491 ms | 0.521 ms | 1.0 | 0.0 | 30 | 100.0% | 100.0% | 0 | $0.00000000 | $0.00000000 |

## Cache State

- `vector`: vector store `local`, cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.
- `hybrid`: vector store `local`, cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.

## Dataset

- Scored cases: 30

## Interpretation

- Best eval-slice result by Hit@5 and mean known-useful rank: `bm25` at 100.0% Hit@5 and mean rank 1.43.
- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive.
- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite.
