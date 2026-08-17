# Query Generation Method Comparison

**Created:** 2026-08-12T01:53:59Z
**Dataset:** `evals/advisor_search_query_cases_enriched_labels.jsonl` (30 exposed development cases)
**Generation model:** `gpt-5.5` for model-driven conditions
**Method version:** `single-query-methods.v2`

This is development evidence, not the reserved holdout decision. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `guided_model_rewrite_v2` | 30/30 | 6942.8 ms | 6591.0 ms | 133056 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `guided_model_rewrite_v2` | `bm25` | 30/30 | 83.3% | 93.3% | 96.7% | 73.3% | 26.7% | 1.241 | 100.4 ms | 0 |
| `guided_model_rewrite_v2` | `hybrid` | 30/30 | 90.0% | 96.7% | 100.0% | 66.0% | 34.0% | 1.2 | 861.7 ms | 0 |

## Misses

- `guided_model_rewrite_v2` / `bm25`: searchq_v1_020
- `guided_model_rewrite_v2` / `hybrid`: none

## Interpretation boundary

Prompts and the corpus guide may be revised using these exposed development cases, with every revision versioned. Final selection should be checked on reserved cases.
