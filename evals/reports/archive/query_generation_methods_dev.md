# Query Generation Method Comparison

**Created:** 2026-08-12T01:53:59Z
**Dataset:** `evals/advisor_search_query_cases_enriched_labels.jsonl` (30 exposed development cases)
**Generation model:** `gpt-5.5` for model-driven conditions
**Method version:** `single-query-methods.v1`

This is development evidence, not the reserved holdout decision. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `raw_question` | 30/30 | 0 ms | 0 ms | 0 |
| `model_rewrite` | 30/30 | 9762.3 ms | 8367.5 ms | 95253 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `raw_question` | `bm25` | 30/30 | 53.3% | 73.3% | 86.7% | 40.7% | 59.3% | 1.808 | 92.8 ms | 0 |
| `raw_question` | `hybrid` | 30/30 | 70.0% | 86.7% | 90.0% | 45.3% | 54.7% | 1.37 | 826.6 ms | 0 |
| `model_rewrite` | `bm25` | 30/30 | 63.3% | 86.7% | 96.7% | 52.0% | 48.0% | 1.621 | 90.2 ms | 0 |
| `model_rewrite` | `hybrid` | 30/30 | 66.7% | 96.7% | 100.0% | 55.3% | 44.7% | 1.433 | 809.3 ms | 0 |

## Misses

- `raw_question` / `bm25`: searchq_v1_003, searchq_v1_020, searchq_v1_022, searchq_v1_026
- `raw_question` / `hybrid`: searchq_v1_003, searchq_v1_010, searchq_v1_020
- `model_rewrite` / `bm25`: searchq_v1_026
- `model_rewrite` / `hybrid`: none

## Interpretation boundary

Prompts and the corpus guide may be revised using these exposed development cases, with every revision versioned. Final selection should be checked on reserved cases.
