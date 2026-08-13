# Eval Methodology Plan

> Historical retrieval-methodology plan. The current open remediation queue is
> maintained in `REMEDIATION_PLAN.md`; use that document for work following the
> completed 46-case query-generation, chunking, embedding-model, and Pinecone
> revalidations.

How we fix the weak spots in how we test retrieval. This is a plan, not a
result. When work here lands, record the outcome in `DESIGN.md` and update the
status boxes below.

## The problem

Our retrieval tests can't tell our methods apart. Three separate reasons:

1. **The tests are too easy.** Every method — plain keyword, vector, hybrid —
   scores near 100% on the current 30 search queries. When everything ties at
   the top, we can't prove one method beats another. So claims like "hybrid is
   best" and "namespaces don't help" really only mean "no measurable difference
   on these tests."

2. **The scoring is too loose.** We grade on Hit@5: the right chunk only has to
   land somewhere in the top 5. In a ~200-chunk library that's easy. A stricter
   grade (did the right chunk come *first*, and at what rank) has more room to
   show a difference.

3. **The answer key is incomplete.** For each query we marked *some* correct
   chunks, not all of them. So a method can return a genuinely good chunk we
   didn't mark and get scored as wrong. Misses can be fake.

Underneath all three: 30 queries is too few to call a small difference real,
even if the scores do separate.

## Why this matters

Everything downstream of retrieval rests on these tests: the choice of hybrid
search, the decision to skip reranking, the decision to keep one combined
library instead of per-layer bins, and the embedding-model comparison we haven't
run yet. If the tests can't separate methods, none of those decisions are as
settled as the narrative sometimes implies. Fixing the tests is what lets us
either earn the stronger claims or honestly downgrade them.

## The work, cheapest first

### Step 1 — Tighten the metric (free)
Re-score the retrieval runs we already have at Hit@1 (right chunk came first)
and mean rank (what position it landed), instead of Hit@5. No new data. If the
scores separate under the stricter grade, we may be done — we'd have our signal
from tests we already ran.

Status: **done.** Result in `evals/reports/retrieval_hit_at_1_rescore.md`. The
slice was only saturated at Hit@5. At Hit@1 the methods separate: hybrid+variants
90.0% vs the BM25 control 80.0% (a flat tie at Hit@5). So the stricter metric
mostly solved the measurement problem — a large new slice may not be needed. Two
caveats carried forward: n=30 is a thin margin, and Hit@1 makes the incomplete
answer key matter more (some misses are fake). Next move is the scoped Step 4
below.

### Step 2 — Mine the misses we already have
We've already recorded real retrieval failures (for example the
fulfillment-cost-for-ads query, where vector and hybrid ranked the wrong chunks
first). Those are proof of where methods actually differ. Turn the failures we
already have into hard test cases before inventing new ones.

Status: **now optional.** Steps 1 and 4 already separated the methods, so hard
cases are no longer needed just to break the tie. If we do add them, the
strongest recorded candidate is 026 — an anecdotal chunk outranks the
explanatory ones for every backend (a real content/chunking weakness). 001's
dense-retrieval weakness is the next candidate.

### Step 3 — Write hard cases on purpose
Add roughly ten cases that are hard for the right reasons:
- **User's words, not the book's words.** Our current queries often reuse the
  exact framework terms from the source, so plain keyword matching wins
  trivially and the smarter methods have nothing to prove. Real users don't
  phrase things like the source.
- **Plausible wrong answers present.** Cases where several chunks look right but
  only one is. That's what forces ranking to matter. If only one chunk is
  obviously correct, every method finds it and they all tie.

Status: **now optional** (see Step 2). Only worth doing if we want a
larger-sample or harder confirmation of the Step 4 result, not to break a tie.

### Step 4 — Fix the answer key on the new cases
When a method returns a chunk we didn't mark, judge whether it's actually a good
answer before calling it a miss. Do this as the hard cases are built, or the new
tests produce fake failures and can't be trusted.

Status: **done.** Full result in
`evals/reports/retrieval_hit_at_1_enriched_rescore.md`; enriched labels in
`evals/advisor_search_query_cases_enriched_labels.jsonl` (originals untouched).
Every backend's non-rank-1 cases were adjudicated by the same rule (add a chunk
only if it directly answers the turn); 9 chunks added across 7 cases. Fair
re-score: BM25 90.0%, vector 86.7%, hybrid+variants 96.7% Hit@1. Enrichment
lifted all three, so it was not selective. Residual real weaknesses: hybrid 1,
BM25 3, vector 4. The one universal weakness is 026, where an anecdotal chunk
outranks the explanatory ones for every backend.

### Step 5 — Set the win condition before running
Write down the rule up front, for example: "hybrid beats the baseline only if it
improves mean rank by at least X, without making latency worse than Y." This
stops us from running everything and then picking whichever metric happens to
favor the method we like. The repo already does this for chunking —
framework-aware was rejected because its gain didn't clear a set threshold.
Apply the same rule here.

Status: not started.

### Step 6 — Enough cases to trust the number
Thirty is too few to call a small difference real. Same lesson as the K=3 model
runs: don't declare a winner inside the noise. Either grow the case count or
state plainly how big a difference the tests can actually detect.

Status: not started.

### Step 7 — Compare embedding models (only after the slice can separate methods)
Once the tests can actually tell methods apart, run the small vs large embedding
comparison (`text-embedding-3-small` vs `text-embedding-3-large`) on that
discriminating slice. Record quality, latency, and cost.

This step is gated on Steps 1–4. Running it earlier is wasted: on the current
easy slice both models score near 100%, so we'd learn nothing and still pay to
embed the whole corpus with the larger model. Unlike Step 1, this one is not
free — it re-runs retrieval and embeds the corpus with each model — so it only
runs once the test can show a result.

If even the harder slice can't separate the two models, the honest result is
"no measurable difference, keep the cheaper small model." On a small corpus with
strong exact-match terms that's a defensible finding, not a failure.

The later comparison held the dimension at Pinecone's 1,536, audited every newly
returned case-passage pair, and revalidated the selected model in an isolated hosted
namespace.

Status: completed; see `evals/reports/embedding_model_comparison.md` and
`evals/reports/pinecone_large_embedding_revalidation.md`.

## The decision at the end

After the steps above, one of two honest outcomes — and picking the right one is
the point:

- **Harder tests separate the methods.** Then we've earned the right to say
  "hybrid genuinely beats the baseline," backed by tests with room to show it.
- **They still tie.** Then we downgrade every retrieval claim to "no measurable
  difference on this corpus; the plain keyword baseline is enough here." On a
  small library with strong exact-match terms, that's a legitimate finding.

What we will not do is run tests where everything ties and still report hybrid as
the winner.

## Recommended path

Do Step 1 first — it's free and might separate the scores on its own. If it
doesn't, do Steps 2–4 on a small batch of about ten deliberately-hard cases
rather than a big expansion. That's the cheapest route to either a real result
or an honest "the baseline is enough."
