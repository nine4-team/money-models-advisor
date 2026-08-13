# Active Framework-Aware Retrieval Matrix

**Date:** 2026-08-12  
**Cases:** 46  
**Chunks:** framework-aware  
**Retrieval:** local, unfiltered, top five  
**Queries:** saved before this replay; no query was regenerated

## Question

Do the earlier query-generation and retriever decisions still hold after replacing
heading-aware chunks with the framework-aware chunks used by the product?

## Method

The same 46 questions and the same saved raw, unguided, and corpus-guided queries
were replayed through BM25 and hybrid retrieval. Each returned framework chunk was
matched to the previously audited heading-aware labels by its source-text span.

Framework boundaries can expose passages that the older retrieval runs never
returned. We therefore reviewed all 115 case-and-passage pairs that had no returned
heading-aware counterpart, plus every transferred positive with weak boundary
overlap. That review corrected 12 missed useful labels and one overly broad useful
label. The adjudications are saved in
`evals/active_query_chunking_adjudications.jsonl`. Codex performed this relevance
review; it was not an independent human review.

## Results

| Query approach | Query model | Retriever | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Raw question | — | BM25 | 56.5% | 76.1% | 87.0% | 1.800 | 41.7% | 58.3% |
| Raw question | — | Hybrid | 63.0% | 80.4% | 87.0% | 1.525 | 50.9% | 49.1% |
| Unguided rewrite | `gpt-5.5` | BM25 | 73.9% | 91.3% | 95.7% | 1.364 | 55.7% | 44.3% |
| Unguided rewrite | `gpt-5.5` | Hybrid | 80.4% | 91.3% | 93.5% | 1.233 | 62.6% | 37.4% |
| Unguided rewrite | `gpt-5.4-mini` | BM25 | 67.4% | 80.4% | 91.3% | 1.619 | 55.2% | 44.8% |
| Unguided rewrite | `gpt-5.4-mini` | Hybrid | 76.1% | 87.0% | 91.3% | 1.333 | 62.6% | 37.4% |
| Corpus-guided rewrite | `gpt-5.5` | BM25 | 89.1% | 95.7% | 95.7% | 1.091 | 76.1% | 23.9% |
| Corpus-guided rewrite | `gpt-5.5` | Hybrid | 93.5% | 97.8% | 100.0% | 1.152 | 78.7% | 21.3% |
| Corpus-guided rewrite | `gpt-5.4-mini` | BM25 | 89.1% | 95.7% | 100.0% | 1.217 | 74.8% | 25.2% |
| Corpus-guided rewrite | `gpt-5.4-mini` | Hybrid | 91.3% | 100.0% | 100.0% | 1.109 | 80.4% | 19.6% |

## Decision

Keep the corpus-guided rewrite and framework-aware chunks. Corpus guidance leads
the raw and unguided controls for both query writers and both retrievers.

Keep hybrid as the product retriever and BM25 as the control. Under both guided
models, hybrid preserves 100% Hit@5 and returns a higher share of useful passages
than BM25. `gpt-5.5` puts a useful passage first slightly more often; Mini reaches a
useful passage within three results on every case and has the highest Useful@5.
Both remain supported for bounded query writing.

The machine-readable summary and per-case results are in
`active_framework_retrieval_matrix_summary.json` and
`active_framework_retrieval_matrix_cases.jsonl`.
