# Diagnostic Embedding Comparison

## Scope

- Query slice: `diagnostic_numeric` from `evals/realistic_queries.jsonl`.
- Diagnostic queries: 6
- Label set: `evals/chunk_relevance_pool.diagnostic_embedding_expansion.jsonl`.
- New `text-embedding-3-large` top-5 query/chunk pairs adjudicated: 7
- `text-embedding-3-large` embedding usage for this expansion: 0 API tokens, 0 API requests, 416 cache hits.

## Results

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.7703 | 0.9333 | 0.5734 |
| `dense-openai-3-small` | 0.5391 | 0.8000 | 0.4773 |
| `hybrid-rrf-3-small` | 0.6886 | 0.9000 | 0.5318 |
| `dense-openai-3-large` | 0.7193 | 0.9000 | 0.5318 |
| `hybrid-rrf-3-large` | 0.7145 | 0.9000 | 0.5318 |

## Per-query nDCG@5

| Query | BM25 | Dense 3-small | Hybrid 3-small | Dense 3-large | Hybrid 3-large |
|---|---:|---:|---:|---:|---:|
| `diagnostic_cfa_level_goal` | 0.903 | 0.677 | 0.760 | 0.647 | 0.744 |
| `diagnostic_continuity_discount_math` | 0.636 | 0.678 | 0.678 | 0.817 | 0.678 |
| `diagnostic_free_offer_overload` | 0.522 | 0.845 | 0.613 | 0.940 | 0.709 |
| `diagnostic_high_revenue_low_margin` | 0.649 | 0.288 | 0.547 | 0.421 | 0.479 |
| `diagnostic_low_first_month_gp` | 1.000 | 0.374 | 0.790 | 0.677 | 0.887 |
| `diagnostic_ltv_good_payback_bad` | 0.913 | 0.372 | 0.744 | 0.815 | 0.790 |

## New Labels Added

| ID | Relevance | Note |
|---|---:|---|
| `diagnostic_cfa_level_goal::context:3` | 2 | Directly supports first-30-day return/CFA implication for acquisition engine. |
| `diagnostic_cfa_level_goal::gross-profit:2` | 1 | Useful gross-profit/LTV context, but not direct first-30-day CFA implication. |
| `diagnostic_continuity_discount_math::continuity-discounts:8` | 2 | Directly discusses earned discount timing and cancellation/stick-rate mechanics. |
| `diagnostic_continuity_discount_math::continuity-discounts:9` | 1 | Cancellation-policy context is adjacent, but weaker than discount/stick-rate chunks. |
| `diagnostic_free_offer_overload::cac:7` | 2 | Directly explains create flow, monetize, then add friction for too many low-quality free leads. |
| `diagnostic_low_first_month_gp::payback-period:6` | 2 | Directly supports shortening payback by increasing upfront gross profit. |
| `diagnostic_ltv_good_payback_bad::payback-period:6` | 2 | Directly supports shortening payback/making money faster when LTV is good but payback is slow. |

## Interpretation

`text-embedding-3-large` improves dense diagnostic retrieval substantially versus `text-embedding-3-small`, but it does not make dense the clear diagnostic winner. BM25 is strongest on this small diagnostic slice, and dense 3-large is close behind. This points toward a diagnostic-specific strategy: either preserve lexical metric matching for numeric cases, rewrite diagnostic queries before dense retrieval, or use a two-stage diagnostic retrieval flow rather than making a global switch to larger embeddings alone.
