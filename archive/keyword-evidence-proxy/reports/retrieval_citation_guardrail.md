# Retrieval Citation Guardrail

## Hypothesis

Hybrid retrieval should not improve ranking metrics at the cost of weaker evidence chunks for cited answers.

## Variants

| Variant | Labeled Queries | Avg Coverage | Full Coverage | Min Coverage | Notes |
|---|---:|---:|---:|---:|---|
| `bm25` | 16 | 90.62% | 68.75% | 50.00% |  |
| `hybrid-rrf` | 16 | 87.50% | 56.25% | 50.00% | 0 API tokens, 218 cache hits |
| `hybrid-rrf-lexical-anchor` | 16 | 90.62% | 68.75% | 50.00% | 0 API tokens, 218 cache hits |

Cost note: this guardrail reuses the same SQLite embedding cache as the retrieval ablation. This run reported 0 API tokens and 218 cache hits for hybrid retrieval.

## Decision

Guardrail allows at most -2 percentage points average coverage or -5 percentage points full-coverage regression versus BM25.

- `hybrid-rrf` fails: avg coverage -3.12%, full coverage -12.50% vs `bm25`.
- `hybrid-rrf-lexical-anchor` passes: avg coverage +0.00%, full coverage +0.00% vs `bm25`.

Decision: `hybrid-rrf-lexical-anchor` is the best citation-preserving hybrid candidate in this run.

Interpretation: plain hybrid RRF did not lose the right chapters; it changed which chunks survived into the final top-k context. Dense retrieval and RRF improved semantic ranking, but in a few cases they pushed out the BM25 chunk containing exact citation terms. The lexical-anchor variant keeps the rank lift while reserving one context slot for BM25's strongest exact-term evidence chunk.

## Per-query Regressions

Regressions shown for `hybrid-rrf`.

- `rollover_upsell` coverage delta -25.00%; missing `competitor`.
- `payback_gross_profit_not_revenue` coverage delta -25.00%; missing `revenue`.
