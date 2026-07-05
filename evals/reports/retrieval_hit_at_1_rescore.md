# Retrieval Re-score at Hit@1 (Step 1 of the eval methodology plan)

This is a **re-score of existing runs**, not a new retrieval run. It reads the
per-case artifacts already on disk and grades them at Hit@1 (was the best marked
chunk ranked first) and full rank distribution, instead of only Hit@5. No model
was called, no retrieval re-run, no embeddings paid for.

It does **not** overwrite the canonical reports. Source artifacts, unchanged:

- `evals/reports/retrieval_backend_comparison_cases.jsonl` (plain generated)
- `evals/reports/retrieval_backend_comparison_generated_variants_local_single_namespace_cases.jsonl` (generated variants)

Motivation and plan: `EVAL_METHODOLOGY_PLAN.md`, Step 1. The concern it tests:
the slice looked saturated because every backend scored ~100% at Hit@5, so no
method could be shown better than another.

## Result — the slice was only saturated at Hit@5

At the stricter grade the methods separate, and in the direction the narrative
claims. n = 30 cases per backend.

### Plain generated queries
| backend | Hit@1 | Hit@3 | Hit@5 | mean rank (hits) |
|---|---:|---:|---:|---:|
| BM25 (control) | 76.7% | 93.3% | 100.0% | 1.43 |
| vector | 66.7% | 96.7% | 96.7% | 1.34 |
| hybrid | 80.0% | 96.7% | 96.7% | 1.21 |

### Generated variants
| backend | Hit@1 | Hit@3 | Hit@5 | mean rank (hits) |
|---|---:|---:|---:|---:|
| BM25 (control) | 80.0% | 96.7% | 100.0% | 1.33 |
| vector | 73.3% | 96.7% | 100.0% | 1.37 |
| **hybrid** | **90.0%** | 100.0% | 100.0% | 1.17 |

Hit@5 shows a flat tie; Hit@1 shows a 10-point gap between hybrid+variants
(90.0%) and the BM25 control (80.0%). Variants also lift every backend's Hit@1
(hybrid 80.0 → 90.0). So tightening the metric mostly solved the measurement
problem — we can tell the methods apart without building a large new slice.

## Two honest caveats

1. **n = 30 is a thin margin.** 90% vs 80% is 3 cases (27 vs 24 of 30). The
   direction is consistent but not bulletproof at this sample size. Retrieval
   here is deterministic (BM25 + cached vectors), so there is no run-to-run
   noise — the only uncertainty is which 30 cases were picked.

2. **Hit@1 makes the incomplete-answer-key problem bite harder.** At Hit@5, a
   good-but-unlabeled chunk at rank 1 was harmless because the labeled chunk was
   still in the top 5. At Hit@1 that same case flips to a "miss." So some Hit@1
   misses are fake — see adjudication below.

## Adjudication — hybrid+variants non-rank-1 cases

Hybrid+variants is non-rank-1 in only 3 of 30 cases. Reading the actual chunk
text:

| case | user turn | rank-1 chunk | verdict |
|---|---|---|---|
| searchq_v1_025 | sell fewer rooms first as a lower-friction version | `feature-downsells:2` — "feature downsells lower prices by changing what the customer gets" | **fake miss** — ideal answer, unlabeled |
| searchq_v1_028 | how do continuity discounts keep people from canceling | `continuity-discounts:7` — "try lifetime discounts at your most common churn point" | **fake miss** — directly answers, unlabeled |
| searchq_v1_026 | pay less now vs a normal discount | `pay-less-now:8` — anecdote about supplements interrupting a talk | **borderline-real** — weak same-chapter chunk outranked the good ones |

After adjudication, hybrid+variants is effectively ~29/30 at Hit@1, with only
026 a genuine ranking wobble. The slice is less saturated than the raw numbers
said, and hybrid is stronger than 90% suggested.

## Fairness caveat — this adjudication is not yet complete

Only hybrid's misses were adjudicated. Adding the good unlabeled chunks that
helped hybrid, without doing the same for BM25 and vector, would rig the
comparison. A complete Step 4 requires adjudicating **every** backend's
non-rank-1 cases, adding any genuinely-good unlabeled chunk to the shared label
set, then re-scoring all three backends against the same enriched labels. Until
that is done, the corrected Hit@1 for hybrid above is a preview, not the final
number.

Non-rank-1 cases needing adjudication for a fair comparison (generated variants):
- BM25: searchq_v1_001, 018, 025, plus the rank-2/3 cases 016, 026
- vector: searchq_v1_002, 004, 023, 025-adjacent, 026, 028, 030
- hybrid: 025, 028 (done — fake), 026 (done — borderline)

## Status

- Step 1 (tighten the metric): **done.** The slice separates methods at Hit@1.
- Step 4 (clean the answer key), scoped down: adjudicate all non-rank-1 cases
  across backends and re-score against enriched labels. **Not started.** This is
  now the next move, and it is small — a bounded set of cases, no new retrieval.
- Whether any deliberately-hard new cases (Steps 2–3) are still needed depends on
  what the fair re-score shows. If hybrid's lead holds after enriching labels for
  all backends, the current slice may be enough to support the claim.
