# Retrieval Backend Comparison Across Query Approaches

**Date:** 2026-08-11
**Cases:** 46
**Query conditions:** Raw question; unguided and corpus-guided rewrites from
`gpt-5.5` and `gpt-5.4-mini`

## Controlled comparison

For each case and query condition, the already-saved query text was sent unchanged to
BM25 and hybrid retrieval. Hybrid sent that same text to its lexical and vector
branches and combined their ranked lists with reciprocal-rank fusion. No query was
regenerated and no subject filter was used. This completes the approach × model ×
retriever matrix instead of testing the backend only after selecting a query method.

All newly surfaced passages and returned positive labels were reviewed under the same
direct-support rule before the final rescore. The completed pooled audit is recorded
in `evals/reports/query_generation_full_matrix_audit.md`.

## Results

| Query approach | Model | Backend | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Raw question | none | BM25 | 54.3% | 69.6% | 84.8% | 1.821 | 40.0% | 60.0% |
| Raw question | none | Hybrid | 65.2% | 82.6% | 84.8% | 1.359 | 44.3% | 55.7% |
| Unguided rewrite | `gpt-5.5` | BM25 | 60.9% | 87.0% | 93.5% | 1.558 | 50.0% | 50.0% |
| Unguided rewrite | `gpt-5.5` | Hybrid | 67.4% | 93.5% | 95.7% | 1.409 | 54.3% | 45.7% |
| Unguided rewrite | `gpt-5.4-mini` | BM25 | 56.5% | 80.4% | 89.1% | 1.561 | 50.4% | 49.6% |
| Unguided rewrite | `gpt-5.4-mini` | Hybrid | 67.4% | 91.3% | 95.7% | 1.455 | 55.2% | 44.8% |
| Corpus-guided rewrite | `gpt-5.5` | BM25 | 84.8% | 93.5% | 97.8% | 1.289 | **74.3%** | **25.7%** |
| Corpus-guided rewrite | `gpt-5.5` | Hybrid | **93.5%** | 97.8% | **100.0%** | 1.130 | 71.7% | 28.3% |
| Corpus-guided rewrite | `gpt-5.4-mini` | BM25 | 84.8% | 95.7% | **100.0%** | 1.326 | 71.7% | 28.3% |
| Corpus-guided rewrite | `gpt-5.4-mini` | Hybrid | 89.1% | **100.0%** | **100.0%** | **1.109** | 71.7% | 28.3% |

## Paired case behavior

| Query condition | Hybrid earlier | BM25 earlier | Same first-useful rank | Hybrid denser | BM25 denser | Same density |
|---|---:|---:|---:|---:|---:|---:|
| Raw question | 12 | 5 | 29 | 19 | 11 | 16 |
| Unguided · `gpt-5.5` | 13 | 8 | 25 | 14 | 10 | 22 |
| Unguided · `gpt-5.4-mini` | 11 | 7 | 28 | 20 | 12 | 14 |
| Corpus-guided · `gpt-5.5` | 6 | 0 | 40 | 13 | 18 | 15 |
| Corpus-guided · `gpt-5.4-mini` | 6 | 1 | 39 | 13 | 14 | 19 |

## Decision

Keep hybrid as the product default and BM25 as the lexical control. Hybrid improves
the raw and both unguided conditions on coverage and evidence density. With the
corpus-guided winner, hybrid ranks useful evidence earlier and preserves complete
Hit@5 coverage. The evidence still does not support claiming that hybrid always
returns a cleaner context: guided BM25 is slightly denser for the `gpt-5.5` query set.

Corpus guidance wins under both backends and both tested models. The query-method
decision and backend decision therefore reinforce one another without requiring a
different retriever for Mini.
