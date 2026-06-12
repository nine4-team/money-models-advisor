# Retrieval Backend Comparison

## Scope

This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.

- Query source: `generated_variants`
- Top K: `5`
- Vector store: `pinecone`
- Namespace policy: `source_need_target_namespaces` for vector/hybrid runs; BM25 does not use vector namespaces.
- Target namespace source: `expected_layers`
- Namespace prefix: `money-models`
- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.
- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.

Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.

## Metrics

| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |
|---|---:|---:|---:|---:|---:|---:|---|
| `bm25` | 5 | 100.0% | 100.0% | 100.0% | 100.0% | 1.4 | none |
| `vector` | 5 | 80.0% | 100.0% | 100.0% | 100.0% | 2.0 | none |
| `hybrid` | 5 | 100.0% | 100.0% | 100.0% | 100.0% | 1.0 | none |

## Performance And Cost

| Backend | p50 Total | p95 Total | p50 Retrieval | p95 Retrieval | p50 Embedding | p95 Embedding | Avg Queries | Avg Variants | Vector Searches | Query Cache Hit Rate | Corpus Cache Hit Rate | API Batches | Estimated Cost | Est. Cost / 1K Queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `bm25` | 2.103 ms | 5.809 ms | 1.782 ms | 5.424 ms | 0 ms | 0.0 ms | 4.0 | 3.0 | 0 | n/a | n/a | 0 | $0.00000000 | $0.00000000 |
| `vector` | 5282.245 ms | 19708.596 ms | 5280.079 ms | 19706.775 ms | 11.844 ms | 13.291 ms | 4.0 | 3.0 | 36 | 100.0% | n/a | 0 | $0.00000000 | $0.00000000 |
| `hybrid` | 5493.388 ms | 19976.952 ms | 5491.868 ms | 19974.789 ms | 9.956 ms | 13.234 ms | 4.0 | 3.0 | 36 | 100.0% | n/a | 0 | $0.00000000 | $0.00000000 |

## Cache State

- `vector`: vector store `pinecone`, cache mode `current`, namespace `openai/text-embedding-3-small`, namespace policy `source_need_target_namespaces`, target namespace source `expected_layers`, query namespaces ``money-models-unit-economics`, `money-models-offers`, `money-models-upsells`, `money-models-continuity`, `money-models-downsells``, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.
- `hybrid`: vector store `pinecone`, cache mode `current`, namespace `openai/text-embedding-3-small`, namespace policy `source_need_target_namespaces`, target namespace source `expected_layers`, query namespaces ``money-models-unit-economics`, `money-models-offers`, `money-models-upsells`, `money-models-continuity`, `money-models-downsells``, query cache complete before run: `True`, cache dir `/Users/benjaminmackenzie/Dev/money-model-architect/.cache/embeddings/openai/text-embedding-3-small`.

## Dataset

- Scored cases: 5

## Interpretation

- Best eval-slice result by Hit@5 and mean known-useful rank: `hybrid` at 100.0% Hit@5 and mean rank 1.0.
- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive.
- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite.
