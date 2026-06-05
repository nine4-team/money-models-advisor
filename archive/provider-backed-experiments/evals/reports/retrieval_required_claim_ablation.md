# Retrieval Required-Claim Ablation

## Hypothesis

Dense and hybrid retrieval should improve semantic ranking without losing chunks that support the human-audited required claims for each eval query.

## Label Set

- Label status included: `accepted`
- Required-claim labels scored: 65
- Top-k context window: 5

## Variants

| Variant | Support Coverage | Unsupported | p95 Latency | Notes |
|---|---:|---:|---:|---|
| `bm25` | 87.69% | 8 | 0.396 ms |  |
| `dense-openai` | 90.77% | 6 | 11.867 ms | OpenAI dense similarity; 0 API tokens, 228 cache hits |
| `hybrid-rrf` | 89.23% | 7 | 10.663 ms | RRF over top 20; 0 API tokens, 228 cache hits |
| `hybrid-rrf-lexical-anchor` | 87.69% | 8 | 10.663 ms | RRF top 4 + BM25 anchor; 0 API tokens, 228 cache hits |

Cost note: embedding vectors are cached in `.cache/embeddings.sqlite3` by model, dimensions, and text hash. This run reported 0 API tokens and 228 cache hits, so warm reruns preserve the experimental signal without repeated embedding spend.

## Decision

Guardrail: a candidate retriever should match or improve BM25 required-claim support coverage before becoming the default retrieval policy.

- `dense-openai` passes: support coverage +3.08% vs `bm25`.
- `hybrid-rrf` passes: support coverage +1.54% vs `bm25`.
- `hybrid-rrf-lexical-anchor` passes: support coverage +0.00% vs `bm25`.

Decision from this experiment alone: `dense-openai` has the strongest required-claim support coverage.

Combined interpretation: this report is the evidence-support guardrail, not the whole retrieval decision. `retrieval_ablation.md` still owns rank quality. A default retriever should improve rank quality and pass this guardrail; in the current measured set, plain `hybrid-rrf` does that, while dense-only is the strongest support-coverage challenger for the next rerank experiment.

## Unsupported Required Claims

### bm25

- `ltgp_cac_viability:ltgp_gt_cac`: The basic viability rule is that lifetime gross profit must exceed CAC; otherwise the business spends more acquiring customers than those customers return.
  Expected one of: `how-businesses-make-money:0`
  Retrieved: `how-businesses-make-money:1`, `gross-profit:2`, `context:1`, `gross-profit:0`, `cfa:0`
- `cfa_levels:level_3`: CFA level 3 is 30-day gross profit greater than 2x CAC, so one customer repays the acquisition cost and funds the next customer.
  Expected one of: `cfa:1`, `cfa:2`
  Retrieved: `cfa:0`, `ride-along-apprenticeship:0`, `context:1`, `gross-profit:3`, `cfa:4`
- `payment_plans:check_desire`: Before extending more terms, confirm the customer still wants the thing; no payment plan solves lack of desire.
  Expected one of: `payment-plans:6`
  Retrieved: `payment-plans:10`, `payment-plans:8`, `payment-plans:9`, `payment-plans:0`, `payment-plans:11`
- `continuity_churn:reminders`: Remind customers as they approach the earn point so the coming discount continues to motivate retention.
  Expected one of: `continuity-discounts:8`
  Retrieved: `continuity-offers:5`, `ten-years-ten-minutes:3`, `waived-fee:0`, `continuity-offers:3`, `continuity-discounts:11`
- `free_offer_cac:watchouts`: Watchouts: free can create more volume than the team can handle and attract people with no intent to buy.
  Expected one of: `cac:4`, `cac:5`
  Retrieved: `cac:2`, `how-businesses-make-money:1`, `context:1`, `cac:12`, `ten-years-ten-minutes:2`
- `free_offer_cac:add_friction`: The recommended control is to create flow first, monetize it, then add friction with qualifications, steps, targeting, required consumption, or longer ads.
  Expected one of: `cac:5`, `cac:6`, `cac:7`
  Retrieved: `cac:2`, `how-businesses-make-money:1`, `context:1`, `cac:12`, `ten-years-ten-minutes:2`
- `free_with_consumption:def`: Free-with-consumption gives away educational content or an experience that provides value, breaks beliefs, builds trust, and leads to the next offer or CTA.
  Expected one of: `free-with-consumption:0`, `free-with-consumption:1`, `free-with-consumption:2`
  Retrieved: `offer-types:3`, `free-with-consumption:4`, `buy-x-get-y:0`, `buy-x-get-y:2`, `cac:1`
- `buy_x_get_y:fit`: It works best when customers can reasonably buy more units or longer access, but requires careful cash management and fulfillment discipline.
  Expected one of: `buy-x-get-y:5`, `buy-x-get-y:7`
  Retrieved: `buy-x-get-y:2`, `buy-x-get-y:4`, `buy-x-get-y:1`, `free-giveaways:4`, `buy-x-get-y:3`

### dense-openai

- `payback_definition:def`: Payback period is how long it takes until gross profit is greater than CAC, i.e. until the acquisition cost breaks even.
  Expected one of: `payback-period:0`
  Retrieved: `payback-period:2`, `payback-period:5`, `payback-period:6`, `payback-period:3`, `ten-years-ten-minutes:2`
- `payback_gross_profit_not_revenue:revenue_false_shortcut`: Using revenue falsely shortens payback; in the example, $160 CAC is paid back in two months from $80 monthly gross profit, not one-and-a-half months from $100 revenue.
  Expected one of: `payback-period:2`
  Retrieved: `gross-profit:4`, `payback-period:1`, `gross-profit:0`, `gross-profit:3`, `payback-period:6`
- `feature_downsell:remove_guarantee`: A strong first move is removing a valuable feature, such as a guarantee, with only a small price drop so the original offer looks better.
  Expected one of: `feature-downsells:1`, `feature-downsells:4`
  Retrieved: `feature-downsells:2`, `feature-downsells:5`, `ten-years-ten-minutes:2`, `downsells:0`, `pay-less-now:8`
- `continuity_churn:reminders`: Remind customers as they approach the earn point so the coming discount continues to motivate retention.
  Expected one of: `continuity-discounts:8`
  Retrieved: `continuity-discounts:11`, `continuity-offers:0`, `continuity-bonus:10`, `continuity-offers:5`, `waived-fee:0`
- `money_model_stack:definition`: A money model is a deliberate sequence of offers designed to minimize CAC, maximize gross profit, and collect it in the first 30 days.
  Expected one of: `money-models-offer-stacks:0`
  Retrieved: `make-your-money-model:1`, `ten-years-ten-minutes:2`, `offer-types:4`, `ten-years-ten-minutes:1`, `free-with-consumption:11`
- `classic_upsell:ethical_boundary`: The upsell should feel essential and helpful, but not be falsely required; the free/advertised item must still be deliverable.
  Expected one of: `classic-upsell:4`
  Retrieved: `classic-upsell:1`, `ten-years-ten-minutes:1`, `menu-upsell:6`, `upsell-offers:1`, `upsell-offers:2`

### hybrid-rrf

- `ltgp_cac_viability:ltgp_gt_cac`: The basic viability rule is that lifetime gross profit must exceed CAC; otherwise the business spends more acquiring customers than those customers return.
  Expected one of: `how-businesses-make-money:0`
  Retrieved: `how-businesses-make-money:1`, `gross-profit:0`, `gross-profit:2`, `context:1`, `cfa:0`
- `cfa_levels:level_3`: CFA level 3 is 30-day gross profit greater than 2x CAC, so one customer repays the acquisition cost and funds the next customer.
  Expected one of: `cfa:1`, `cfa:2`
  Retrieved: `cfa:0`, `context:1`, `cfa:4`, `ride-along-apprenticeship:0`, `money-models-offer-stacks:0`
- `payback_gross_profit_not_revenue:revenue_false_shortcut`: Using revenue falsely shortens payback; in the example, $160 CAC is paid back in two months from $80 monthly gross profit, not one-and-a-half months from $100 revenue.
  Expected one of: `payback-period:2`
  Retrieved: `payback-period:1`, `how-businesses-make-money:2`, `payback-period:0`, `gross-profit:4`, `payback-period:6`
- `payment_plans:check_desire`: Before extending more terms, confirm the customer still wants the thing; no payment plan solves lack of desire.
  Expected one of: `payment-plans:6`
  Retrieved: `payment-plans:10`, `payment-plans:0`, `payment-plans:1`, `payment-plans:9`, `payment-plans:11`
- `continuity_churn:reminders`: Remind customers as they approach the earn point so the coming discount continues to motivate retention.
  Expected one of: `continuity-discounts:8`
  Retrieved: `continuity-offers:5`, `continuity-discounts:11`, `waived-fee:0`, `continuity-discounts:7`, `continuity-bonus:9`
- `free_offer_cac:watchouts`: Watchouts: free can create more volume than the team can handle and attract people with no intent to buy.
  Expected one of: `cac:4`, `cac:5`
  Retrieved: `cac:2`, `cac:12`, `ten-years-ten-minutes:2`, `how-businesses-make-money:1`, `context:1`
- `free_offer_cac:add_friction`: The recommended control is to create flow first, monetize it, then add friction with qualifications, steps, targeting, required consumption, or longer ads.
  Expected one of: `cac:5`, `cac:6`, `cac:7`
  Retrieved: `cac:2`, `cac:12`, `ten-years-ten-minutes:2`, `how-businesses-make-money:1`, `context:1`

### hybrid-rrf-lexical-anchor

- `payback_definition:def`: Payback period is how long it takes until gross profit is greater than CAC, i.e. until the acquisition cost breaks even.
  Expected one of: `payback-period:0`
  Retrieved: `payback-period:2`, `payback-period:6`, `payback-period:5`, `payback-period:3`, `how-businesses-make-money:2`
- `ltgp_cac_viability:ltgp_gt_cac`: The basic viability rule is that lifetime gross profit must exceed CAC; otherwise the business spends more acquiring customers than those customers return.
  Expected one of: `how-businesses-make-money:0`
  Retrieved: `how-businesses-make-money:1`, `gross-profit:0`, `gross-profit:2`, `context:1`, `cfa:0`
- `cfa_levels:level_3`: CFA level 3 is 30-day gross profit greater than 2x CAC, so one customer repays the acquisition cost and funds the next customer.
  Expected one of: `cfa:1`, `cfa:2`
  Retrieved: `cfa:0`, `context:1`, `cfa:4`, `ride-along-apprenticeship:0`, `gross-profit:3`
- `payment_plans:check_desire`: Before extending more terms, confirm the customer still wants the thing; no payment plan solves lack of desire.
  Expected one of: `payment-plans:6`
  Retrieved: `payment-plans:10`, `payment-plans:0`, `payment-plans:1`, `payment-plans:9`, `payment-plans:8`
- `continuity_churn:reminders`: Remind customers as they approach the earn point so the coming discount continues to motivate retention.
  Expected one of: `continuity-discounts:8`
  Retrieved: `continuity-offers:5`, `continuity-discounts:11`, `waived-fee:0`, `continuity-discounts:7`, `ten-years-ten-minutes:3`
- `free_offer_cac:watchouts`: Watchouts: free can create more volume than the team can handle and attract people with no intent to buy.
  Expected one of: `cac:4`, `cac:5`
  Retrieved: `cac:2`, `cac:12`, `ten-years-ten-minutes:2`, `how-businesses-make-money:1`, `context:1`
- `free_offer_cac:add_friction`: The recommended control is to create flow first, monetize it, then add friction with qualifications, steps, targeting, required consumption, or longer ads.
  Expected one of: `cac:5`, `cac:6`, `cac:7`
  Retrieved: `cac:2`, `cac:12`, `ten-years-ten-minutes:2`, `how-businesses-make-money:1`, `context:1`
- `buy_x_get_y:fit`: It works best when customers can reasonably buy more units or longer access, but requires careful cash management and fulfillment discipline.
  Expected one of: `buy-x-get-y:5`, `buy-x-get-y:7`
  Retrieved: `buy-x-get-y:2`, `buy-x-get-y:4`, `buy-x-get-y:3`, `buy-x-get-y:1`, `free-giveaways:4`
