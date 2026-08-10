# Open Items

Plain-language list of what's left. This is the working tracker. The
requirement-by-requirement mapping in `JD_REQUIREMENTS_AUDIT.md` has the full
detail, but it's dense and it lags behind the latest work; this file is the
quick read.

## To build

### 1. Compare embedding models
Right now vector search uses one OpenAI embedding model (`text-embedding-3-small`).
We never checked whether the bigger one (`text-embedding-3-large`) retrieves
better, and at what cost and speed. Run both over the same search tests and
record quality, latency, and cost.

Blocked by the test-set problem below: our current search tests are too easy to
show a difference between embedding models. It has to run *after* the tests can
separate methods, so it's tracked as Step 7 in `EVAL_METHODOLOGY_PLAN.md` — that
doc owns the ordering.

### 2. Write one observability report
We have cost, token, latency, and cache numbers, but they're spread across
separate retrieval and model-routing reports. Pull them into one report
(`evals/reports/ai_observability.md`): cost per request, token use, quality
signals, cache hit rate, latency, and a few "this looks wrong" flags with clear
thresholds. The job description asks for this directly. We now have the tiering
data to feed it.

### 3. Score answer quality
Every other layer has an automatic scorer. The final answer the advisor writes
does not — it's only reviewed by hand in the product-smoke report. Add a rubric
so answer quality gets scored like everything else.

## Methodological weakness to fix

### Our search tests are too easy — mostly addressed
The 30-case slice looked saturated because it was graded at Hit@5, where every
method scores ~100%. Re-scoring the existing runs at Hit@1, plus a fair label
cleanup, separates the methods: hybrid+variants 96.7% Hit@1 vs the BM25 control
90.0% vs vector 86.7%, with hybrid carrying only 1 residual real weakness against
BM25's 3 and vector's 4. So "hybrid is best" now holds on this corpus, and the
embedding comparison (Step 7) is unblocked — it can run on the Hit@1 grade.

What's left is optional: build deliberately-hard cases for a larger-sample or
harder confirmation (n=30 gives thin margins). Not needed to break the tie.
Record and plan in `EVAL_METHODOLOGY_PLAN.md` and the two
`evals/reports/retrieval_hit_at_1_*` reports.

## Report writing

### Finish the narrative clarity + compression pass
The `narrative.html` report is mid-edit. A compression pass removed duplicated
summary layers and cross-section echoes; still open are a full clarity re-pass
(hold every line to "a cold reader understands it," not just "no jargon"),
tightening the remaining content-heavy prose, and deleting dead CSS. Detail and
status: `NARRATIVE_CLARITY_PASS.md` (Round 2).

## Cheap cleanup

### Reconcile the stale docs
`JD_REQUIREMENTS_AUDIT.md` and `GOLDEN_DATASET.md` were written before the K=3
model-tiering work (narrative §3.10). They still call the cheaper-tier and
multi-provider comparison "open," when §3.10 now has a finished K=3 tier sweep
and a routing decision (Sonnet for the source-need call, Opus for tool-use
orchestration). Update both docs to match.

## Decided — not doing (recorded so we don't re-litigate)

- **Whole-turn latency tracking.** We only ever measured retrieval time and
  harness-reported proxy time, not full advisor-turn time. Backfilling it means
  re-running the model tests and burning a lot of tokens for a small gain. Skip.
- **Namespace splitting at runtime.** The code exists and works, but tests
  showed splitting the source library into per-layer bins retrieves the same
  results as one combined bin, and slightly slower — even when we hand it the
  perfect bin every time. Kept off on purpose. See DESIGN.md.
- **TypeScript / web / API surface.** The job description asks for it, but this
  repo's rule puts hosted-agent and web-product code in the separate hosted repo
  (`money-models-advisor-hosted`). Out of scope here, not a gap.
- **CI regression gate.** A command that runs the stable tests and fails on
  regression would be nice for production optics, but it's low-signal for a
  portfolio investigation record. Only if the final submission needs it.
