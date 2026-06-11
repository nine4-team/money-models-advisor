# Retrieval Backend Comparison

## Scope

This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.

- Query source: `generated_variants`
- Top K: `5`
- Vector store: `pinecone`
- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.
- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.

Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.

## Metrics

| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |
|---|---:|---:|---:|---:|---:|---:|---|
| `bm25` | 30 | 96.7% | 100.0% | 100.0% | 100.0% | 1.3 | none |
| `vector` | 30 | 96.7% | 100.0% | 100.0% | 100.0% | 1.43 | none |
| `hybrid` | 30 | 100.0% | 100.0% | 100.0% | 100.0% | 1.17 | none |

## Performance And Cost

| Backend | p50 Total | p95 Total | p50 Retrieval | p95 Retrieval | p50 Embedding | p95 Embedding | Avg Queries | Avg Variants | Vector Searches | Query Cache Hit Rate | Corpus Cache Hit Rate | API Batches | Estimated Cost | Est. Cost / 1K Queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `bm25` | 0.753 ms | 2.017 ms | 0.651 ms | 1.92 ms | 0.0 ms | 0.0 ms | 4.0 | 3.0 | 0 | n/a | n/a | 0 | $0.00000000 | $0.00000000 |
| `vector` | 5493.787 ms | 6232.051 ms | 5493.19 ms | 6230.259 ms | 11.154 ms | 14.619 ms | 4.0 | 3.0 | 120 | 100.0% | n/a | 0 | $0.00000000 | $0.00000000 |
| `hybrid` | 5333.258 ms | 6466.091 ms | 5332.178 ms | 6465.213 ms | 9.395 ms | 12.89 ms | 4.0 | 3.0 | 120 | 100.0% | n/a | 0 | $0.00000000 | $0.00000000 |

## Cache State

- `vector`: vector store `pinecone`, cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.
- `hybrid`: vector store `pinecone`, cache mode `current`, namespace `openai/text-embedding-3-small`, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.

## Dataset

- Scored cases: 30

## Interpretation

- Best eval-slice result by Hit@5 and mean known-useful rank: `hybrid` at 100.0% Hit@5 and mean rank 1.17.
- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive.
- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite.
