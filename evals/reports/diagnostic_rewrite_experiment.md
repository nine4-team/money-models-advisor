# Diagnostic Rewrite Experiment

## Hypothesis

Numeric diagnostic questions should retrieve better when the system first identifies the economic bottleneck and rewrites the query toward the relevant metrics/frameworks.

## Results

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.7017 | 0.9333 | 0.4269 |
| `dense-openai-3-small` | 0.4890 | 0.8000 | 0.3636 |
| `hybrid-rrf-3-small` | 0.6238 | 0.9000 | 0.4084 |
| `dense-openai-3-large` | 0.6548 | 0.9000 | 0.4084 |
| `hybrid-rrf-3-large` | 0.6536 | 0.9000 | 0.4084 |
| `diagnose-rewrite-bm25` | 0.9142 | 0.9667 | 0.4454 |

## Rewrites

| Query | Constraint | Rewritten query |
|---|---|---|
| `diagnostic_low_first_month_gp` | `monetization` | diagnose monetization: first 30 day gross profit client-financed acquisition cfa payback period upsell offers. Reason: First-30-day gross profit does not cover CAC, so the model cannot finance acquisition inside the first month. Success metric: Increase first-30-day gross profit until it covers CAC, then push toward 2x CAC. |
| `diagnostic_high_revenue_low_margin` | `gross-margin` | diagnose gross-margin: gross profit gross margin delivery cost service business margin. Reason: Service gross margin is 30%, below the 80% rule of thumb. Success metric: Get service gross margin to 80%+ before layering more offers. |
| `diagnostic_ltv_good_payback_bad` | `cash-constraint` | diagnose cash-constraint: lifetime gross profit to CAC is healthy but payback period is slow. Retrieve payback period, first 30 day gross profit, client-financed acquisition, upfront gross profit, upsell offers. |
| `diagnostic_free_offer_overload` | `free-offer-quality` | diagnose free front-end offer quality: lower CAC, free leads, lead volume overload, booking rate drop, add friction after creating flow, monetize then filter |
| `diagnostic_continuity_discount_math` | `continuity-retention` | diagnose continuity retention: members cancel after month three, permanent discount after month three, improve churn, extend lifetime gross profit, continuity discounts, earned discount timing |
| `diagnostic_cfa_level_goal` | `scale-ready` | diagnose scale-ready: client-financed acquisition level 3 first 30 day gross profit acquisition engine scale spend. Reason: First-30-day gross profit is at least 2x CAC, so acquisition is client-financed at Level 3. Success metric: Protect conversion and churn while scaling spend. |

## Per-query nDCG@5

| Query | BM25 | Dense 3-small | Hybrid 3-small | Dense 3-large | Hybrid 3-large | Diagnose rewrite |
|---|---:|---:|---:|---:|---:|---:|
| `diagnostic_low_first_month_gp` | 1.000 | 0.374 | 0.790 | 0.677 | 0.887 | 1.000 |
| `diagnostic_high_revenue_low_margin` | 0.427 | 0.190 | 0.360 | 0.277 | 0.316 | 0.815 |
| `diagnostic_ltv_good_payback_bad` | 0.913 | 0.372 | 0.744 | 0.815 | 0.790 | 1.000 |
| `diagnostic_free_offer_overload` | 0.522 | 0.845 | 0.613 | 0.940 | 0.709 | 0.952 |
| `diagnostic_continuity_discount_math` | 0.446 | 0.476 | 0.476 | 0.573 | 0.476 | 0.903 |
| `diagnostic_cfa_level_goal` | 0.903 | 0.677 | 0.760 | 0.647 | 0.744 | 0.815 |

## Decision

If the diagnose-first rewrite improves over raw BM25 and embedding retrieval, keep it as the diagnostic retrieval policy. If it only matches BM25, prefer the simpler lexical diagnostic route until answer-level evals justify the extra diagnostic logic.
