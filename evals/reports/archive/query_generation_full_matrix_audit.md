# Query Generation Full-Matrix Relevance Audit

**Date:** 2026-08-11
**Scope:** Raw question plus unguided and corpus-guided rewrites from `gpt-5.5`
and `gpt-5.4-mini`, each evaluated through BM25 and hybrid retrieval over 46 cases

## Integrity boundary

The earlier query-generation comparison held retrieval constant on hybrid, and the
first backend comparison tested only the winning corpus-guided method. This audit
completed the missing BM25 cells for the raw question and both unguided query writers.
It reused every saved query; no query was regenerated.

The three completed cells contributed 690 frozen top-five result slots. Their pool
contained 145 case-passage pairs that had not appeared in the previously audited
hybrid or guided-backend pools. Each was reviewed using the same rule: a passage is
useful only when it directly supports a substantial part of the requested answer;
topic or vocabulary overlap alone is insufficient.

The completed cells returned 159 unique positive case-passage pairs. Prior audits had
already reviewed 158 of them. The one newly surfaced positive was rechecked and
removed. A consistency check also found one earlier removal that a later audit had
accidentally restored; that bookkeeping error was corrected before rescoring.

All retrieval output was frozen before these label changes, and the same corrected
answer key was applied to every method, model, and backend. Codex performed the
semantic review with the question and passage visible, not an independent human
reviewer.

## False-negative corrections

Thirteen newly surfaced passages directly support their cases:

| Case | Added passage | Direct support found |
|---|---|---|
| `searchq_v1_005` | `offer-types:4`, `offer-types:5` | Upsells follow the attraction offer and maximize immediate profit; the applied example shows the sequence. |
| `searchq_v1_009` | `how-businesses-make-money:1` | Directly contrasts CAC with lifetime and first-month gross profit. |
| `searchq_v1_014` | `payback-period:1` | Explains the immediate post-purchase buying window for complementary offers. |
| `searchq_v1_024` | `offer-types:3` | Gives a concrete ordered downsell flow after the full offer is rejected. |
| `searchq_v1_025` | `decoy-offers:4` | Describes offering fewer components as a lower-friction version of a premium offer. |
| `searchq_v1_030` | `offer-types:3` | Shows attraction, upsell, downsell, continuity, and prepayment working as one stack. |
| `querygen_holdout_v1_001` | `waived-fee:2` | Gives an alternative churn-point mechanism that makes leaving before the target term costlier than staying. |
| `querygen_holdout_v1_006` | `free-trials:3` | Provides the implementation process for letting a skeptical prospect experience the service before committing. |
| `querygen_holdout_v1_007` | `payment-plans:2`, `feature-downsells:5` | Covers financing and the explicit transition to payment timing when the offer is affordable overall but not today. |
| `querygen_holdout_v1_008` | `classic-upsell:2` | Demonstrates the natural-complement pattern: customers need the adjacent product after the first purchase. |
| `querygen_holdout_v1_012` | `ten-years-ten-minutes:2` | Explicitly defines lowering price by removing quantity, quality, or optional components. |

The other 132 newly surfaced pairs were rejected because they described adjacent
offer types, supplied only generic framework background, or repeated query vocabulary
without supporting the requested mechanism or comparison.

## False-positive corrections

| Case | Removed passage | Why it does not qualify |
|---|---|---|
| `searchq_v1_021` | `buy-x-get-y:0` | It is introductory story material and does not address whether fulfillment cost makes the offer viable. |
| `searchq_v1_004` | `upsell-offers:2` | It only lists upsell types and does not distinguish an attraction offer from an upsell. An earlier audit had marked it removed, but a later metadata update accidentally restored it. |

## Final shared-label result

| Query approach | Model | Retriever | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Raw question | none | BM25 | 54.3% | 69.6% | 84.8% | 1.821 | 40.4% | 59.6% |
| Raw question | none | Hybrid | 67.4% | 82.6% | 84.8% | 1.308 | 44.8% | 55.2% |
| Unguided rewrite | `gpt-5.5` | BM25 | 60.9% | 87.0% | 93.5% | 1.558 | 50.9% | 49.1% |
| Unguided rewrite | `gpt-5.5` | Hybrid | 67.4% | 93.5% | 95.7% | 1.409 | 57.0% | 43.0% |
| Unguided rewrite | `gpt-5.4-mini` | BM25 | 56.5% | 80.4% | 89.1% | 1.561 | 51.3% | 48.7% |
| Unguided rewrite | `gpt-5.4-mini` | Hybrid | 67.4% | 91.3% | 95.7% | 1.432 | 55.7% | 44.3% |
| Corpus-guided rewrite | `gpt-5.5` | BM25 | 84.8% | 93.5% | 97.8% | 1.289 | **75.2%** | **24.8%** |
| Corpus-guided rewrite | `gpt-5.5` | Hybrid | **93.5%** | 97.8% | **100.0%** | 1.130 | 73.0% | 27.0% |
| Corpus-guided rewrite | `gpt-5.4-mini` | BM25 | 84.8% | 95.7% | **100.0%** | 1.326 | 72.2% | 27.8% |
| Corpus-guided rewrite | `gpt-5.4-mini` | Hybrid | 89.1% | **100.0%** | **100.0%** | **1.109** | 72.6% | 27.4% |

Corpus guidance wins under both retrieval backends and both tested query models.
Hybrid improves the raw and unguided conditions on both coverage and evidence density.
For the guided winner, hybrid ranks useful evidence earlier and preserves complete
Hit@5; BM25 remains slightly denser for the `gpt-5.5` queries. The selected runtime
therefore remains one corpus-guided query through hybrid retrieval.
