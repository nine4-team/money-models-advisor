# Query Generation Model Comparison

**Date:** 2026-08-11
**Selected method:** Corpus-guided rewrite v2
**Models:** `gpt-5.5` and `gpt-5.4-mini`

## Question

After selecting the corpus-guided query-generation method, can the smaller model used
elsewhere in the project preserve its retrieval quality?

## Controlled comparison

The model is the only intended variable. Both conditions used:

- the same corpus-guided v2 prompt and versioned corpus guide;
- the same saved business snapshots;
- one generated query per case;
- no subject or namespace filter;
- the same local hybrid retriever and top-five cutoff;
- the same shared relevance labels.

Every prompt, response, query, and retrieval result is preserved under
`evals/runs/query_generation/v2/` and
`evals/runs/query_generation/holdout_v1/`.

## Results

| Cases | Model | Valid | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---|---:|---:|---:|---:|---:|
| 30 development | `gpt-5.5` | 30/30 | **90.0%** | **96.7%** | 100.0% | **1.200** |
| 30 development | `gpt-5.4-mini` | 30/30 | 86.7% | **100.0%** | 100.0% | **1.133** |
| 16-case expansion | `gpt-5.5` | 16/16 | **100.0%** | **100.0%** | 100.0% | **1.000** |
| 16-case expansion | `gpt-5.4-mini` | 16/16 | 93.8% | **100.0%** | 100.0% | 1.062 |

Both models always found useful evidence within five results. `gpt-5.5` put it first
more often, while Mini reached it within three results on every case.

Hit@5 does not measure how much of the five-result context is useful. Because the
advisor receives all five passages, the comparison also measures evidence density:
Precision@5 is the percentage of the five returned passages that are labeled useful,
and Noise@5 is its complement.

| Cases | Model | Mean useful passages / 5 | Precision@5 | Noise@5 |
|---|---|---:|---:|---:|
| 30 development | `gpt-5.5` | 3.30 | 66.0% | 34.0% |
| 30 development | `gpt-5.4-mini` | **3.40** | **68.0%** | **32.0%** |
| 16-case expansion | `gpt-5.5` | **4.13** | **82.5%** | **17.5%** |
| 16-case expansion | `gpt-5.4-mini` | 3.94 | 78.8% | 21.2% |

Across all 46 cases, the models tie at 165 useful passages each. Mini returned fewer
useful passages in 9 cases, the same number in 28, and more in 9. The backend audit
that produced the final shared labels is recorded in
`evals/reports/retrieval_backend_relevance_audit.md`; no query or retrieval output was
changed during that review.

## Harness efficiency

| Cases | Model | Mean generation latency | p50 generation latency | Codex-reported tokens |
|---|---|---:|---:|---:|
| 30 development | `gpt-5.5` | **6.94 s** | **6.59 s** | **133,056** |
| 30 development | `gpt-5.4-mini` | 9.07 s | 8.63 s | 174,240 |
| 16-case expansion | `gpt-5.5` | **6.74 s** | **5.84 s** | **72,139** |
| 16-case expansion | `gpt-5.4-mini` | 9.35 s | 9.78 s | 169,512 |

The token counts are Codex subscription-harness proxies, not API billing. They do not
establish dollar cost. In this harness, however, Mini provided neither a latency nor a
token-use advantage.

## Ranking and density pattern

Across the combined suite, `gpt-5.5` ranked the first useful passage earlier in three
cases, Mini did so in two, and they tied in 41. `gpt-5.5` nevertheless has the higher
Hit@1 because its three wins cross the first-rank threshold; Mini's wins improve the
mean rank and complete Hit@3. Retrieval evidence therefore does not identify a clear
quality loser.

## Does the approach choice survive the model change?

Yes. The unguided rewrite was also run with Mini so the generated approaches form a
complete two-model comparison.

| Cases | Mini approach | Hit@1 | Hit@3 | Hit@5 | Precision@5 | Noise@5 |
|---|---|---:|---:|---:|---:|---:|
| 30 development | Unguided | 66.7% | 96.7% | 100.0% | 56.0% | 44.0% |
| 30 development | Corpus-guided | **86.7%** | **100.0%** | **100.0%** | **68.0%** | **32.0%** |
| 16-case expansion | Unguided | 68.8% | 81.2% | 87.5% | 53.8% | 46.2% |
| 16-case expansion | Corpus-guided | **93.8%** | **100.0%** | **100.0%** | **78.8%** | **21.2%** |

Guidance improves Mini as well as `gpt-5.5`. This rules out the immediate concern that
the selected query approach only wins with the larger model. It does not change the
model decision: that comparison still holds the selected guided approach fixed.

## Decision status

The model choice is not settled by these retrieval metrics. Both models reached 100%
Hit@5 and returned the same total number of useful passages across 46 cases. The
product gives all five passages to the answering agent, so neither the Hit@1 difference
nor the per-slice density differences establish a final-answer-quality difference. The
runtime remains unchanged on `gpt-5.5` while that question is open; Mini is a validated
bounded alternative, not yet a production promotion.

The next comparison should hold the answering model and answer prompt fixed, provide
it each query model's frozen top-five evidence, and score required-claim support,
citation correctness, unsupported claims, and answer usefulness. If final-answer
quality is equivalent, Mini remains a viable query-generation choice. Precision@5 is
also only an evidence-density measure: several useful passages can repeat one idea, so
it does not replace required-claim coverage.
