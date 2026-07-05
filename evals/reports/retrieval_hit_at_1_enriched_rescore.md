# Retrieval Hit@1 — Fair Enriched Re-score (methodology plan, Step 4)

This completes the Step 1 re-score honestly. Step 1 graded the existing runs at
Hit@1 and found the methods separate, but the incomplete answer key made some
Hit@1 misses fake. This step fixes that for **every** backend, not just the one
we liked, then re-scores all three against the same enriched labels.

Still a re-score of existing runs — no retrieval re-run, no model calls, no
embeddings paid for. Nothing canonical was overwritten:

- Original labels untouched: `evals/advisor_search_query_cases.jsonl`
- Enriched labels in a new file: `evals/advisor_search_query_cases_enriched_labels.jsonl`
- Per-case run artifacts unchanged: `retrieval_backend_comparison_generated_variants_local_single_namespace_cases.jsonl`
- Step 1 preview: `retrieval_hit_at_1_rescore.md`

## Method

For every case where a backend's best labeled chunk was not at rank 1, the chunk
sitting above it was read in full and judged by one rule: **add it to the labels
only if it directly and substantially answers the user turn** — something we'd
cite. Chunks that merely mention the topic were not added. The same rule was
applied to BM25, vector, and hybrid, so no backend gets a friendlier answer key
than another.

Adjudicating only one backend's misses would rig the comparison. This is the
fair version.

## Chunks added — 9 across 7 cases

| case | user turn | added | why |
|---|---|---|---|
| searchq_v1_001 | fulfillment cost and whether ads work | `cfa:0` | ties CAC / gross profit / payback to advertising viability |
| searchq_v1_004 | attraction offer vs upsell | `upsell-offers:2` | says upsell structures can also be front-ends |
| searchq_v1_016 | why an expensive option first helps sell | `anchor-upsell:2`, `anchor-upsell:4` | the anchoring principle and its execution |
| searchq_v1_023 | decoy offer into a premium package | `decoy-offers:2` | worked decoy → premium example |
| searchq_v1_025 | sell fewer rooms as a lower-friction version | `feature-downsells:2`, `feature-downsells:4` | defines feature downsell + the process |
| searchq_v1_026 | pay less now vs a normal discount | `pay-less-now:9` | the pay-now discount mechanism |
| searchq_v1_028 | continuity discounts stop canceling | `continuity-discounts:7` | lifetime discount at the churn point |

## Result

n = 30 cases per backend. Generated variants, local single namespace.

| backend | Hit@1 before | Hit@1 after | Hit@3 after | Hit@5 after | mean rank after |
|---|---:|---:|---:|---:|---:|
| BM25 (control) | 80.0% | 90.0% | 100.0% | 100.0% | 1.13 |
| vector | 73.3% | 86.7% | 96.7% | 100.0% | 1.20 |
| **hybrid+variants** | 90.0% | **96.7%** | 100.0% | 100.0% | **1.03** |

Enrichment lifted all three backends (BM25 +10.0, vector +13.4, hybrid +6.7), so
the label cleanup was fair, not selective. Hybrid+variants still leads.

The clearer signal than the Hit@1 percentage is the count of genuine weaknesses
left after the fake misses are removed:

| backend | real non-rank-1 cases left | which |
|---|---:|---|
| hybrid+variants | 1 | 026 |
| BM25 | 3 | 008, 018, 026 |
| vector | 4 | 001, 002, 026, 030 |

## Surviving real weaknesses

- **026 (all three backends).** "Pay less now vs a normal discount." An anecdotal
  chunk, `pay-less-now:8` (a story about supplement interruptions), ranks first
  for every backend, above the explanatory chunks. This is a content/chunking
  issue, not a query issue — a natural candidate for a deliberately-hard case.
- **001 (vector).** The documented dense weakness: vector ranks CAC chunks above
  the gross-profit answer and never retrieves `cfa:0`, so the label enrichment
  that helped BM25 does not help vector here.
- **018 (BM25).** Lexical match on "attraction offer" pulls the general
  build-process chunk above the specific free-vs-discounted answer.
- **002, 030 (vector), 008 (BM25).** Minor: a weakly-related chunk outranks the
  labeled one by a single position; not citeable enough to add.

## Caveats

- **n = 30, thin margins.** Hybrid 29/30 vs BM25 27/30 is a 2-case gap. The
  direction is consistent across before and after enrichment, but this is not a
  large-sample result. The residual-weakness count (1 vs 3 vs 4) and mean rank
  (1.03 vs 1.13 vs 1.20) are steadier signals than the raw percentage.
- **Deterministic retrieval.** BM25 and cached vectors have no run-to-run noise,
  so repeated sampling (K>1) does not apply; the only uncertainty is the case
  sample.

## Conclusion

After a fair label cleanup, hybrid+variants genuinely leads at Hit@1 on this
corpus — it is not the flat Hit@5 tie the saturated grade showed. It has one
residual weakness against BM25's three and vector's four. BM25 as a control
remains strong (90.0%), which is the honest finding for a small corpus with
strong exact-match framework terms: hybrid wins, but not by a landslide, and the
baseline is not embarrassed.

Whether to build the deliberately-hard cases (methodology plan Steps 2–3) is now
optional: the metric change plus fair adjudication already separated the methods.
The one universal weakness (026) is the strongest single candidate if we do add
hard cases.
