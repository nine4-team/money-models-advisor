# Retrieval Backend Relevance-Label Audit

> Historical guided-only audit. The later full approach × model × retriever pool
> supersedes its final metrics; see `evals/reports/query_generation_full_matrix_audit.md`.

**Date:** 2026-08-11
**Scope:** Frozen corpus-guided queries from `gpt-5.5` and `gpt-5.4-mini`, each run through BM25 and hybrid retrieval over all 46 cases

## Integrity boundary

All 92 queries and all 184 top-five retrieval lists were frozen before this
review. The query text was not regenerated, retrieval was not rerun after labels
were inspected, and the same corrected labels were applied to every query writer
and backend.

The audit reviewed all 460 BM25 result slots (327 unique case-passage pairs),
including 157 pairs that were not labeled useful when the review began. Every
previously positive label returned by BM25 was also rechecked. A passage qualifies
only when it directly supports a substantial part of the user's question; topic
overlap alone does not count. Codex performed the semantic review with the question
and passage visible, so this is transparent method-neutral adjudication rather than
an independent human review.

## False-negative corrections

Fifty-nine directly useful case-passage labels were added:

| Case | Added passages | Direct support found |
|---|---|---|
| `searchq_v1_001` | `how-businesses-make-money:1`, `cfa:1`, `payback-period:1` | Revenue-versus-gross-profit, the 30-day gross-profit/CAC threshold, and delivery-cost payback math. |
| `searchq_v1_002` | `how-businesses-make-money:2`, `payback-period:0`, `cfa:3`, `gross-profit:0` | The CFA inputs, payback definition, reinvestment mechanism, and gross-profit side of acquisition. |
| `searchq_v1_003` | `gross-profit:0`, `payback-period:1` | Gross profit available for acquisition and a concrete CAC/delivery-cost payback example. |
| `searchq_v1_004` | `offer-types:4`, `upsell-offers:1`, `upsell-offers:2` | Attraction/upsell objectives, post-sale profit mechanics, and the fact that offer roles can be recombined. |
| `searchq_v1_005` | `payback-period:1` | The immediate post-purchase buying window and its payback effect. |
| `searchq_v1_007` | `payment-plans:2`, `payment-plans:7` | Financing and spreading payment timing without shrinking the offer. |
| `searchq_v1_008` | `free-trials:3` | The implementation sequence for a trial conditioned on required actions. |
| `searchq_v1_009` | `context:1`, `gross-profit:3`, `gross-profit:4`, `payback-period:1` | CAC-versus-gross-profit framing, the two acquisition levers, variable-cost definition, and payback math. |
| `searchq_v1_010` | `free-with-consumption:0`, `:1`, `:11` | Free education as an attraction offer and how to place it before a sales conversation. |
| `searchq_v1_011` | `how-businesses-make-money:0`, `:2`, `payback-period:0`, `:1`, `cfa:0` | Why gross profit—not revenue—must cover CAC and how delivery cost affects payback. |
| `searchq_v1_013` | `waived-fee:1`, `:5` | Startup/onboarding-fee structure and its upfront-cash tradeoff. |
| `searchq_v1_014` | `upsell-offers:1` | The timing rule: offer the add-on after the new problem is present. |
| `searchq_v1_015` | `menu-upsell:2` | The A/B choice, card-on-file, and prescription mechanics of a menu upsell. |
| `searchq_v1_016` | `anchor-upsell:3`, `:5` | Why anchoring changes the reference price and concrete premium-versus-standard examples. |
| `searchq_v1_019` | `free-giveaways:2`, `:4` | Giveaway execution and advanced prize/offer mechanics. |
| `searchq_v1_022` | `free-with-consumption:10` | The beliefs free education must change before a paid offer is appropriate. |
| `searchq_v1_023` | `decoy-offers:5`, `:6` | Contrast sizing and the transition from the decoy into the premium offer. |
| `searchq_v1_024` | `feature-downsells:1`, `ten-years-ten-minutes:2`, `payment-plans:10` | Reduced-scope, payment-plan, and ordered-downsell paths after a no. |
| `searchq_v1_025` | `ten-years-ten-minutes:2` | A concise definition of lowering price by changing what the customer receives. |
| `searchq_v1_026` | `payment-plans:1`, `pay-less-now:6` | Timing versus price and the conditional pay-now/pay-later structure. |
| `searchq_v1_027` | `continuity-offers:2` | How commitment and recurring payment extend lifetime gross profit. |
| `searchq_v1_028` | `continuity-offers:3` | How a purchased lower rate reduces churn and increases lifetime value. |
| `searchq_v1_030` | `make-your-money-model:2`, `offer-types:5` | One-at-a-time implementation and applied examples of the complete stack. |
| `querygen_holdout_v1_004` | `cfa:2`, `payback-period:1` | The cash-limitation threshold and a concrete beginning-of-customer payback example. |
| `querygen_holdout_v1_007` | `payment-plans:7` | Spreading payment timing while preserving the full service. |
| `querygen_holdout_v1_008` | `classic-upsell:0`, `:1`, `upsell-offers:0` | The natural-complement pattern and its post-purchase placement. |
| `querygen_holdout_v1_011` | `how-businesses-make-money:2` | CAC, gross profit, and payback as the acquisition-capacity inputs. |
| `querygen_holdout_v1_015` | `offer-types:4`, `upsell-offers:0` | Attraction as the lead-engagement stage, distinguished from later upsells. |
| `querygen_holdout_v1_016` | `make-your-money-model:0` | Starting with one model before weaving multiple offers together. |

Rejected additions included adjacent offer types, generic framework summaries that did
not answer the requested relationship, and passages that repeated query vocabulary
without supplying the requested mechanism.

## False-positive correction

One prior label was removed:

| Case | Removed passage | Why it does not qualify |
|---|---|---|
| `searchq_v1_029` | `continuity-offers:6` | It explains the value of recurring revenue and merely names bonus offers; it does not explain what kind of bonus would make the membership more valuable. |

No other positive label returned by BM25 failed the direct-support rule.

## Final method-neutral rescore

| Query writer | Backend | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---:|---:|---:|---:|---:|---:|
| `gpt-5.5` | BM25 | 84.8% | 93.5% | 97.8% | 1.289 | **74.3%** | **25.7%** |
| `gpt-5.5` | Hybrid | **93.5%** | **97.8%** | **100.0%** | **1.130** | 72.2% | 27.8% |
| `gpt-5.4-mini` | BM25 | 84.8% | 95.7% | **100.0%** | 1.326 | **72.2%** | **27.8%** |
| `gpt-5.4-mini` | Hybrid | **89.1%** | **100.0%** | **100.0%** | **1.109** | **72.2%** | **27.8%** |

Hybrid improved first-useful rank in 6 of 46 GPT-5.5 cases and never lost; with
Mini it improved 6, lost 1, and tied 39. Evidence density did not move in one
direction: BM25 returned more useful top-five passages in 17 GPT-5.5 cases versus 13
for hybrid, and in 14 Mini cases versus 13 for hybrid. The backend decision therefore
rests on earlier useful evidence and complete top-five coverage, not a claim that
hybrid always produces a cleaner context.
