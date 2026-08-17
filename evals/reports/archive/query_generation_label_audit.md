# Query Generation Relevance-Label Audit

**Date:** 2026-08-10
**Scope:** Raw-question, unguided-rewrite, and corpus-guided-rewrite hybrid results over the 30 exposed development cases

## Purpose

The retrieval scores are meaningful only if a passage counted as relevant actually helps
answer the user's question and if directly useful retrieved passages are not missing from
the answer key. This audit therefore checks both directions:

- **False negatives:** unlabeled passages ranked above the first labeled passage, plus
  every top-five passage for a miss.
- **False positives:** every labeled case-passage pair returned in the top five by any
  of the three current methods.

The reviewer could see the question and passage identity, so this is a transparent
development-set review rather than independent blind adjudication. A passage is useful
only when it directly supports a substantial part of the requested explanation,
comparison, mechanism, or recommendation. Merely naming the same topic or a neighboring
framework is insufficient.

All corrections modify the shared case labels. No method receives its own answer key.

## False-negative corrections

| Case | Added passage | Reason |
|---|---|---|
| `searchq_v1_005` | `make-your-money-model:0`, `make-your-money-model:1` | The worked stack and build process place the upsell after the front-end offer and connect the stack to first-30-day cash. |
| `searchq_v1_010` | `upsell-offers:0` | The opening distinguishes the attraction offer that gets leads to engage from the later upsell. |
| `searchq_v1_012` | `cfa:2` | It directly explains how more than 2x CAC in first-30-day gross profit funds the next customer and compounds acquisition. |
| `searchq_v1_023` | `decoy-offers:4` | It gives concrete decoy-versus-premium examples and explains the contrast mechanism. |
| `searchq_v1_024` | `feature-downsells:5` | Its summary explains the feature-downsell sequence and when to transition to payment-plan downselling. |
| `searchq_v1_026` | `pay-less-now:3` | It explains the pay-later versus discounted-pay-now structure, bonuses, and cash timing. |

Rejected additions included generic payback definitions for a membership question,
onboarding-fee framing that did not explain faster payback, neighboring credit/refund
mechanisms for a Win Your Money Back question, and payment mechanisms that would blur
the requested Pay Less Now comparison.

## False-positive corrections

The initial audit inventory contained 104 labeled case-passage pairs returned in the
top five across the three current methods. Four labels across three cases failed the
same direct-support rule:

| Case | Removed passage | Reason |
|---|---|---|
| `searchq_v1_004` | `upsell-offers:2` | It only lists upsell types; it does not distinguish an attraction offer from an upsell. |
| `searchq_v1_012` | `cfa:0`, `context:1` | They explain general CFA or the 1x threshold, not what the requested 2x threshold means. |
| `searchq_v1_015` | `upsell-offers:2` | It names classic and menu upsells but explains neither method nor their difference. |

The other returned positive labels were retained. After applying the removals and the
new direct `cfa:2` label, the current result lists contain 101 unique labeled
case-passage pairs.

## Final method-neutral re-score

All queries and retrieval outputs were reused from their preserved artifacts. Nothing
was regenerated and retrieval was not rerun.

| Current method · hybrid retrieval | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw user question | 63.3% | 86.7% | 90.0% | 1.444 |
| Unguided model rewrite | 60.0% | 93.3% | 96.7% | 1.517 |
| Corpus-guided model rewrite | **90.0%** | **96.7%** | **100.0%** | **1.200** |

The corpus-guided rewrite is the development leader. This report records the exposed
development stage; the later reserved-case comparison and its bidirectional label audit
are recorded in `query_generation_holdout_v1.md` and
`query_generation_holdout_v1_label_audit.md`.

## Mini unguided robustness extension — 2026-08-11

The later unguided `gpt-5.4-mini` condition was generated and retrieved before its
labels were reviewed. Its top-five results added 29 case-passage pairs that had not
appeared in the three-method audit above. All 29 were reviewed under the same
direct-support rule, including both previously labeled and unlabeled pairs.

Three false negatives were corrected:

| Case | Added passage | Reason |
|---|---|---|
| `searchq_v1_009` | `payback-period:0` | Directly defines payback as gross profit exceeding CAC, which bears on the requested CAC-versus-gross-profit diagnosis. |
| `searchq_v1_010` | `decoy-offers:8` | Summarizes a decoy attraction offer that gets leads to engage before presenting the premium offer. |
| `searchq_v1_024` | `downsells:1` | States when a downsell fits and why it works when price, rather than the product, causes the no. |

No false-positive labels were removed. The frozen Mini retrievals were rescored without
regenerating a query or rerunning retrieval: 60.0% Hit@1, 96.7% Hit@3, 100.0% Hit@5,
46.7% Precision@5, and 53.3% Noise@5.
