# Query Generation Holdout Relevance-Label Audit

**Date:** 2026-08-10
**Scope:** Raw-question, unguided-rewrite, and corpus-guided-rewrite hybrid results over 16 reserved cases

## Purpose and integrity boundary

The 48 queries and their retrieval results were generated and frozen before this
review. The review then checked the shared answer key in both directions:

- **False negatives:** a returned passage was missing from the labels even though it
  directly supported a substantial part of the user's question.
- **False positives:** a prior label merely shared a topic or named a framework but
  did not directly help answer the question.

The same corrected labels apply to all three methods. No query was regenerated and no
retrieval was rerun after inspecting the results. The review covered all 163 unique
case-passage pairs returned in the top five by any method and every prior positive
label: 167 unique pairs in total.

Codex performed the semantic review with the question and passage identity visible.
This is therefore a transparent, method-neutral audit—not independent human
adjudication.

## False-negative corrections

Forty-four directly useful passages were added:

| Case | Added passages | Why they qualify |
|---|---|---|
| `querygen_holdout_v1_001` | `continuity-discounts:11` | Summarizes placing and promoting a lifetime discount at the usual churn month. |
| `querygen_holdout_v1_002` | `waived-fee:4`, `waived-fee:5` | Explain why the fee increases commitment and how fee size changes uptake. |
| `querygen_holdout_v1_003` | `continuity-bonus:3`, `:4`, `:5`, `:10`, `:11`, `:12` | Cover the upfront bonus, relatedness, price contrast, commitment, and advertising mechanics that make continuity easier to sell. |
| `querygen_holdout_v1_004` | `context:1`, `cfa:1` | Directly state the cash-timing problem and the first-30-day recovery condition. |
| `querygen_holdout_v1_006` | `free-with-consumption:4`, `:5`, `:10`, `:11`, `free-trials:1`, `:2`, `:4` | The wording supports both useful coaching or education before the sale and a structured service trial. |
| `querygen_holdout_v1_007` | `payment-plans:4`, `:10`, `pay-less-now:2`, `ten-years-ten-minutes:2` | All preserve the offer while changing when payment or delivery occurs. |
| `querygen_holdout_v1_008` | `menu-upsell:0`, `payback-period:3` | Explain prescribing the natural next need and the timing of a nutrition upsell. |
| `querygen_holdout_v1_009` | `buy-x-get-y:3` | Gives the exact prepaid-months-plus-bonus-months structure. |
| `querygen_holdout_v1_010` | `decoy-offers:3`, `:4`, `:7`, `:8` | Give the mechanism, a concrete stripped-down comparison, presentation guidance, and the summary rule. |
| `querygen_holdout_v1_011` | `gross-profit:3`, `cfa:0` | Connect product and shipping costs to gross profit and acquisition capacity. |
| `querygen_holdout_v1_012` | `feature-downsells:1`, `:5`, `downsells:0`, `:1` | Directly distinguish removing value from discounting the unchanged product and describe the narrow exception. |
| `querygen_holdout_v1_013` | `rollover-upsell:2`, `:4`, `:5`, `ten-years-ten-minutes:2` | State that prior spend can be credited toward a larger next offer and explain application and pricing. |
| `querygen_holdout_v1_014` | `anchor-upsell:3`, `:5` | Explain the effect of the anchor and give a premium-versus-standard example matching the question. |
| `querygen_holdout_v1_015` | `cac:6` | Shows that a stronger attraction offer can create more sales without changing close rate. |
| `querygen_holdout_v1_016` | `offer-types:4`, `:5` | Explicitly says the stack does not happen all at once and that a business need not deploy all four offer types. |

Case `querygen_holdout_v1_005` required no additions.

## False-positive corrections

Seven overly broad labels were removed:

| Case | Removed passages | Why they do not qualify |
|---|---|---|
| `querygen_holdout_v1_001` | `continuity-discounts:0` | Introduces free time for a commitment but not the churn-point mechanism asked about. |
| `querygen_holdout_v1_003` | `continuity-offers:2` | Discusses contracts and LTV generally, not an onboarding bonus that helps sell continuity. |
| `querygen_holdout_v1_008` | `classic-upsell:1` | Describes monetizing a free item, not the post-purchase nutrition need in the question. |
| `querygen_holdout_v1_010` | `decoy-offers:0` | The returned chunk is introductory story material and does not explain the comparison mechanism. |
| `querygen_holdout_v1_012` | `feature-downsells:0` | Contains only transcript markup, not substantive guidance. |
| `querygen_holdout_v1_015` | `make-your-money-model:0`, `offer-types:5` | Describe the overall stack and an example without diagnosing attraction as the failed stage. |

## Final method-neutral re-score

| Method · hybrid retrieval | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw user question | 56.2% | 75.0% | 75.0% | 1.333 |
| Unguided model rewrite | 68.8% | 87.5% | 87.5% | 1.357 |
| Corpus-guided model rewrite | **100.0%** | **100.0%** | **100.0%** | **1.000** |

The corpus-guided method remains the clear winner after the bidirectional audit. It
ranked a directly useful passage first for every reserved case.

## Mini unguided robustness extension — 2026-08-11

The later unguided `gpt-5.4-mini` condition was generated and retrieved before its
labels were reviewed. It introduced 19 case-passage pairs not covered by the frozen
three-method audit above. All 19 were reviewed under the same direct-support rule,
including both previously labeled and unlabeled pairs.

Three false negatives were corrected:

| Case | Added passage | Reason |
|---|---|---|
| `querygen_holdout_v1_004` | `payback-period:6` | Shows how upfront gross profit shortens payback and relieves the beginning-of-customer cash constraint. |
| `querygen_holdout_v1_009` | `continuity-bonus:11` | Directly describes prepaid months plus bonus months as an upfront-cash structure and explains the commitment tradeoff. |
| `querygen_holdout_v1_011` | `payback-period:0` | Defines scalable acquisition in terms of gross profit recovering CAC, rather than revenue alone. |

No false-positive labels were removed. The frozen Mini retrievals were rescored without
regenerating a query or rerunning retrieval: 68.8% Hit@1, 81.2% Hit@3, 87.5% Hit@5,
52.5% Precision@5, and 47.5% Noise@5. The two remaining misses are
`querygen_holdout_v1_005` and `querygen_holdout_v1_016`.
