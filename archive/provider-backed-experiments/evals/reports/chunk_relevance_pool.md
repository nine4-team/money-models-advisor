# Chunk Relevance Pool

## Purpose

This file records the candidate chunk pool for blind relevance review. Each row is a query/chunk pair collected from candidate retrievers over the realistic query set.

The reviewer should not use retriever provenance while labeling. Provenance is stored in the JSONL so metrics can be computed after review.

## Build Summary

- Query set: `evals/realistic_queries.jsonl`
- Queries: 36
- Unique query/chunk pairs: 312
- Retriever top-k: 5
- Fusion top-k: 20
- Output: `evals/chunk_relevance_pool.jsonl`

## Variants

| Variant | Queries Covered | Retrieved Rows |
|---|---:|---:|
| `bm25` | 36 | 180 |
| `dense-openai` | 36 | 180 |
| `hybrid-rrf` | 36 | 180 |

## Cost Note

Embedding usage: 955 API tokens, 1 API requests, 440 cache hits.

## Label Rubric

| Label | Meaning |
|---:|---|
| 0 | The chunk is not useful for answering this query. |
| 1 | The chunk is partially useful or background context, but not enough by itself. |
| 2 | The chunk directly supports a good answer to the query. |
