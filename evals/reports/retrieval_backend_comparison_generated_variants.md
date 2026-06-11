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
| `bm25` | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 1.2 | none |
| `vector` | 10 | 90.0% | 100.0% | 100.0% | 100.0% | 1.5 | none |
| `hybrid` | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 1.0 | none |

## Dataset

- Scored cases: 10

## Interpretation

- Best seed result by Hit@5 and mean known-useful rank: `hybrid` at 100.0% Hit@5 and mean rank 1.0.
- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive.
- If vector or hybrid underperform BM25 on this seed set, inspect misses before changing the active backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite.
