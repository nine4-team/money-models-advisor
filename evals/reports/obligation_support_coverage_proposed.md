# Required Claim Support Coverage

## Hypothesis

Retrieval should return chunks that support the required claims a human expects for each eval query.

## Label Set

- Label status included: `accepted+proposed`
- Required-claim labels scored: 65

## Results

| Strategy | Required Claims | Support Coverage | Unsupported | p50 Latency |
|---|---:|---:|---:|---:|
| `bm25-heading-aware` | 65 | 87.69% | 8 | 0.223 ms |

## Unsupported Required Claims

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

## Decision

Use accepted required-claim support coverage as the primary retrieval-support guardrail.
