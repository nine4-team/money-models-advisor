# Guided V2 Retrieval Label Sanity Check

**Date:** 2026-08-10
**Scope:** Guided-v2 BM25 and hybrid results over the 30 exposed development cases

## Purpose

This check asks whether the existing non-exhaustive relevance labels incorrectly mark
directly useful retrieved passages as irrelevant. It reviews every unlabeled passage
ranked above the first labeled passage in guided-v2 BM25 or hybrid output, plus every
top-five passage for a backend miss.

This is a development-set sanity check, not an independent blind adjudication. The
reviewer could see the user question and passage identity. The acceptance rule is the
same one used for the earlier enriched-label pass: add a passage only when it directly
and substantially answers the turn and would be reasonable to cite. Merely mentioning
the same topic or a neighboring framework is insufficient.

Any accepted chunk is added to the shared case label, not to a method-specific answer
key. All preserved methods must be re-scored against the same corrected labels.

## Accepted additions

| Case | Added chunk | Reason |
|---|---|---|
| `searchq_v1_005` | `make-your-money-model:0`, `make-your-money-model:1` | The worked stack and five-step build process directly place an upsell after the front-end offer and connect the stack to first-30-day cash. |
| `searchq_v1_010` | `upsell-offers:0` | Its opening explicitly distinguishes attraction offers as the front-end offers that get leads to engage before explaining the later upsell step. |
| `searchq_v1_023` | `decoy-offers:4` | It gives concrete decoy-versus-premium examples and explains that larger contrast moves buyers toward the premium option. |
| `searchq_v1_024` | `feature-downsells:5` | Its summary directly describes the feature-downsell and payment-plan sequence after rejection of the main offer. |
| `searchq_v1_026` | `pay-less-now:3` | It directly explains the pay-later price versus discounted-pay-now structure, bonuses, and cash-timing objective. |

## Rejected candidates

| Case | Rejected chunks | Reason |
|---|---|---|
| `searchq_v1_006` | `how-businesses-make-money:2` | Defines CAC, gross profit, and payback but does not connect recurring membership or continuity to payback. |
| `searchq_v1_013` | `waived-fee:2` | Explains onboarding-fee framing and fee waiver for commitment, but not the requested faster-payback mechanism. |
| `searchq_v1_020` | `rollover-upsell:1`, `rollover-upsell:2`, `rollover-upsell:3`, `cfa:2`, `pay-less-now:5` | These are neighboring credit, refund, acquisition, or delayed-payment concepts; none explains how the named Win Your Money Back offer works. |
| `searchq_v1_021` | `ten-years-ten-minutes:1` | Summarizes Buy X Get Y Free but does not address whether expensive fulfillment makes it economically appropriate. |
| `searchq_v1_026` | `waived-fee:1`, `payment-plans:1` | Describe different offer mechanics and would blur the requested comparison. |

## Interpretation boundary

The accepted additions correct known false negatives in the development labels. They
do not justify further prompt tuning or replace the required pre-generation human
review of the untouched holdout labels.

## Method-neutral re-score

All saved v1 and v2 queries were re-scored from their existing retrieval artifacts;
no query was regenerated and no retrieval was rerun.

| Hybrid condition | Hit@1 before | Hit@1 after | Hit@3 after | Hit@5 after |
|---|---:|---:|---:|---:|
| Raw question | 66.7% | 66.7% | 86.7% | 90.0% |
| Unguided rewrite | 63.3% | 66.7% | 93.3% | 96.7% |
| Guided v1 | 73.3% | 76.7% | 93.3% | 93.3% |
| Guided v2 | 86.7% | 93.3% | 96.7% | 100.0% |

Guided v2 now ties guided v1 on 24 cases, improves four existing ranks, repairs both
v1 top-five misses, and regresses none. Its two non-rank-1 cases are `searchq_v1_013`
at rank 2 and `searchq_v1_020` at rank 4. The older four-query, reviewer-assisted
ceiling remains 96.7% Hit@1 and 100.0% Hit@3/Hit@5.
