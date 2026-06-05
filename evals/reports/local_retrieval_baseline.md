# Local Retrieval Baseline

## Hypothesis

A lightweight local BM25-style retriever over heading-aware transcript chunks should provide a runnable baseline for the five-layer namespace taxonomy before dense embeddings, Pinecone, hybrid retrieval, or reranking are introduced.

## Variant

- `local-bm25-heading-aware`
- Dataset: `evals/golden.jsonl`
- Top-k: `5`
- Chunks indexed: `202`

## Metrics

| Metric | Value |
|---|---:|
| Total queries | 32 |
| Hit@1 | 81.25% |
| Hit@5 | 100.00% |
| MRR | 0.8917 |
| p50 retrieval latency | 0.495 ms |
| p95 retrieval latency | 1.726 ms |

## Per-query Results

| ID | Layer | Expected | Rank | Top retrieved |
|---|---|---|---:|---|
| `payback_definition` | `unit-economics` | payback-period | 2 | how-businesses-make-money, payback-period, cfa |
| `rollover_upsell` | `upsells` | rollover-upsell | 1 | rollover-upsell, upsell-offers, rollover-upsell |
| `continuity_churn` | `continuity` | continuity-discounts | 5 | continuity-offers, ten-years-ten-minutes, waived-fee |
| `feature_downsell` | `downsells` | feature-downsells | 2 | ten-years-ten-minutes, feature-downsells, feature-downsells |
| `free_offer_cac` | `unit-economics` | cac | 1 | cac, how-businesses-make-money, context |
| `cac_fully_loaded` | `unit-economics` | cac | 1 | cac, cfa, context |
| `gross_profit_service_margin` | `unit-economics` | gross-profit | 1 | gross-profit, gross-profit, how-businesses-make-money |
| `ltgp_cac_viability` | `unit-economics` | how-businesses-make-money | 1 | how-businesses-make-money, gross-profit, context |
| `cfa_levels` | `unit-economics` | cfa | 1 | cfa, ride-along-apprenticeship, context |
| `payback_gross_profit_not_revenue` | `unit-economics` | payback-period | 1 | payback-period, how-businesses-make-money, payback-period |
| `offer_types_four` | `offers` | offer-types | 1 | offer-types, ten-years-ten-minutes, offer-types |
| `attraction_liquidate_cac` | `offers` | attraction-offers, offer-types | 1 | offer-types, make-your-money-model, cac |
| `win_your_money_back` | `offers` | win-your-money-back | 2 | free-giveaways, win-your-money-back, win-your-money-back |
| `free_giveaway_structure` | `offers` | free-giveaways | 1 | free-giveaways, free-giveaways, free-giveaways |
| `decoy_offer` | `offers` | decoy-offers | 1 | decoy-offers, decoy-offers, decoy-offers |
| `free_with_consumption` | `offers` | free-with-consumption | 2 | offer-types, free-with-consumption, buy-x-get-y |
| `buy_x_get_y` | `offers` | buy-x-get-y | 1 | buy-x-get-y, buy-x-get-y, buy-x-get-y |
| `upsell_overview` | `upsells` | upsell-offers | 1 | upsell-offers, payback-period, upsell-offers |
| `classic_upsell` | `upsells` | classic-upsell | 1 | classic-upsell, classic-upsell, ten-years-ten-minutes |
| `menu_upsell` | `upsells` | menu-upsell | 1 | menu-upsell, menu-upsell, menu-upsell |
| `anchor_upsell` | `upsells` | anchor-upsell | 1 | anchor-upsell, anchor-upsell, anchor-upsell |
| `rollover_competitor` | `upsells` | rollover-upsell | 1 | rollover-upsell, rollover-upsell, rollover-upsell |
| `downsells_overview` | `downsells` | downsells, feature-downsells | 1 | downsells, downsells, feature-downsells |
| `payment_plans` | `downsells` | payment-plans | 1 | payment-plans, payment-plans, payment-plans |
| `free_trial_penalty` | `downsells` | free-trials | 1 | free-trials, free-trials, offer-types |
| `feature_downsell_guarantee` | `downsells` | feature-downsells | 1 | feature-downsells, feature-downsells, feature-downsells |
| `pay_less_now` | `downsells` | pay-less-now | 1 | pay-less-now, pay-less-now, free-trials |
| `continuity_overview` | `continuity` | continuity-offers | 1 | continuity-offers, continuity-offers, continuity-offers |
| `continuity_bonus` | `continuity` | continuity-bonus | 1 | continuity-bonus, continuity-bonus, continuity-bonus |
| `continuity_discount` | `continuity` | continuity-discounts | 1 | continuity-discounts, continuity-discounts, continuity-discounts |
| `waived_fee` | `continuity` | waived-fee | 1 | waived-fee, waived-fee, ten-years-ten-minutes |
| `money_model_stack` | `offers` | money-models-offer-stacks, offer-types | 3 | make-your-money-model, make-your-money-model, offer-types |

## Decision

Use this as the local baseline. Future chunking, embedding, hybrid retrieval, and reranking experiments must beat this run on retrieval quality while staying inside latency and complexity guardrails.

## Failure Analysis

- No hit@5 failures in this run.

## Next Experiment

Run the chunking comparison so the baseline can be tested against fixed-window and framework-aware variants.
