# Advisor Search-Query Quality Eval

## Scope

This eval covers only turns where source-material search is the correct next action. It does not evaluate whether the agent should search in the first place; that is covered by the next-action classification eval.

The known-useful chunk labels are seed relevance labels, not exhaustive relevance judgments. A miss means the query did not retrieve one of the labeled citeable chunks, not that every returned chunk is useless.

## Dataset

- Cases: 10
- Splits: {'dev': 9, 'scenario_holdout': 1}
- Retrieval purposes: {'comparison_evidence': 1, 'diagnostic_evidence': 2, 'recommendation_evidence': 4, 'teaching_evidence': 3}

## Validation

- Status: passed

## Metrics

- Known-useful Hit@3: 100.0%
- Known-useful Hit@5: 100.0%
- Top-1 layer match: 100.0%
- Any expected-layer chunk in top 5: 100.0%
- Average focus-term recall in query text: 0.760
- Duplicate query strings: none

## Case Table

| Case | Split | Purpose | Expected Layers | Query | Top Chunks | Known Useful Rank | Focus Recall |
|---|---|---|---|---|---|---:|---:|
| `searchq_v1_001` | `dev` | `teaching_evidence` | unit-economics | fulfillment cost gross profit CAC payback first 30 days | `how-businesses-make-money:2`, `cfa:0`, `cfa:1`, `payback-period:6`, `context:1` | 1 | 0.80 |
| `searchq_v1_002` | `dev` | `teaching_evidence` | unit-economics | client financed acquisition first 30 days gross profit CAC | `context:1`, `cfa:0`, `cfa:1`, `how-businesses-make-money:2`, `gross-profit:0` | 1 | 1.00 |
| `searchq_v1_003` | `dev` | `diagnostic_evidence` | unit-economics | how much can spend on ads first 30 day gross profit CAC | `gross-profit:0`, `context:1`, `cfa:0`, `cfa:1`, `payback-period:0` | 2 | 0.40 |
| `searchq_v1_004` | `scenario_holdout` | `comparison_evidence` | offers, upsells | attraction offer upsell difference front end offer after first sale | `make-your-money-model:0`, `make-your-money-model:1`, `upsell-offers:0`, `continuity-bonus:3`, `cac:12` | 1 | 0.80 |
| `searchq_v1_005` | `dev` | `recommendation_evidence` | upsells | upsell after first sale next offer maximize 30 day profits | `upsell-offers:0`, `upsell-offers:1`, `money-models-offer-stacks:0`, `payback-period:3`, `offer-types:5` | 1 | 1.00 |
| `searchq_v1_006` | `dev` | `recommendation_evidence` | continuity | continuity recurring gross profit improve payback period recurring offer | `payback-period:6`, `payback-period:0`, `continuity-offers:2`, `payback-period:2`, `payback-period:1` | 1 | 1.00 |
| `searchq_v1_007` | `dev` | `recommendation_evidence` | downsells | payment plan downsell pay less now customer decides terms | `payment-plans:0`, `payment-plans:10`, `payment-plans:1`, `payment-plans:8`, `ten-years-ten-minutes:2` | 1 | 0.60 |
| `searchq_v1_008` | `dev` | `teaching_evidence` | offers, downsells | free trial penalty attraction offer lead engage consumption | `make-your-money-model:0`, `make-your-money-model:1`, `free-trials:1`, `free-trials:5`, `free-trials:2` | 1 | 0.40 |
| `searchq_v1_009` | `dev` | `diagnostic_evidence` | unit-economics | CAC gross profit make more money per customer customer worth acquisition | `gross-profit:0`, `context:1`, `cfa:1`, `gross-profit:3`, `how-businesses-make-money:2` | 1 | 0.80 |
| `searchq_v1_010` | `dev` | `recommendation_evidence` | offers | attraction offer front end get leads to engage free discount | `make-your-money-model:1`, `make-your-money-model:0`, `decoy-offers:3`, `attraction-offers:0`, `pay-less-now:2` | 1 | 0.80 |

## Decision

Use this as the first source-search query-quality baseline. Do not compare dense or hybrid retrieval until the query cases and seed labels are reviewed, because retrieval-model differences are hard to interpret when the query formulation itself is unstable.

## Next Work

Review broad or low-focus queries, then update `ADVISOR_QUERY_POLICY_V1.md` and the query builder so generated queries are driven by the current source need rather than snapshot status alone.
