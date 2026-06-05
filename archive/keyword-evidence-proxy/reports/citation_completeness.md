# Citation Completeness

## Hypothesis

A chunking strategy may be worth adopting even when retrieval rank barely improves if its retrieved chunks contain more complete citation evidence for the final answer.

## Variants

| Strategy | Labeled Queries | Avg Coverage | Full Coverage | Min Coverage | Chunks | Avg Words |
|---|---:|---:|---:|---:|---:|---:|
| `heading-aware` | 16 | 90.62% | 68.75% | 50.00% | 202 | 513.5 |
| `framework-aware` | 16 | 85.94% | 50.00% | 50.00% | 204 | 496.9 |

## Decision

`heading-aware` is the metric winner on evidence coverage. The adopted default is `heading-aware` because adoption requires at least +5 percentage points average coverage or +10 percentage points full-coverage rate over `heading-aware`.

Measured delta vs `heading-aware`: avg coverage +0.00%, full coverage +0.00%.

## Per-query Misses

### `heading-aware`

- `free_offer_cac` coverage 75.00%; missing `friction`.
- `gross_profit_service_margin` coverage 75.00%; missing `cost of goods`.
- `cfa_levels` coverage 50.00%; missing `level 1`, `level 3`.
- `payment_plans` coverage 75.00%; missing `afford`.
- `continuity_bonus` coverage 75.00%; missing `first month`.

### `framework-aware`

- `rollover_upsell` coverage 75.00%; missing `competitor`.
- `free_offer_cac` coverage 75.00%; missing `friction`.
- `gross_profit_service_margin` coverage 75.00%; missing `cost of goods`.
- `cfa_levels` coverage 50.00%; missing `level 1`, `level 3`.
- `payback_gross_profit_not_revenue` coverage 75.00%; missing `revenue`.
- `payment_plans` coverage 75.00%; missing `third-party financing`.
- `continuity_bonus` coverage 75.00%; missing `subscription`.
- `continuity_discount` coverage 75.00%; missing `ACH`.

## Next Experiment

Move to retrieval ablation: BM25-only vs dense-only vs hybrid. Keep citation completeness as a guardrail so better rank does not come at the cost of weaker evidence chunks.
