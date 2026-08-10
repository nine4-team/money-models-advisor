# Query Generation Method Comparison

**Created:** 2026-08-10T18:59:38Z
**Dataset:** `evals/advisor_search_query_cases_enriched_labels.jsonl` (30 exposed development cases)
**Generation model:** `gpt-5.5` for model-driven conditions
**Method version:** `single-query-methods.v1`

This is development evidence, not the untouched holdout decision. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `raw_question` | 30/30 | 0 ms | 0 ms | 0 |
| `model_rewrite` | 30/30 | 9762.3 ms | 8367.5 ms | 95253 |
| `guided_model_rewrite` | 30/30 | 8455.1 ms | 7732.6 ms | 174530 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete 30-case rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `raw_question` | `bm25` | 30/30 | 46.7% | 66.7% | 76.7% | 1.783 | 92.8 ms | 0 |
| `raw_question` | `hybrid` | 30/30 | 66.7% | 86.7% | 90.0% | 1.407 | 826.6 ms | 0 |
| `model_rewrite` | `bm25` | 30/30 | 50.0% | 70.0% | 90.0% | 2.037 | 90.2 ms | 0 |
| `model_rewrite` | `hybrid` | 30/30 | 63.3% | 90.0% | 96.7% | 1.552 | 809.3 ms | 0 |
| `guided_model_rewrite` | `bm25` | 30/30 | 66.7% | 90.0% | 93.3% | 1.429 | 91.7 ms | 0 |
| `guided_model_rewrite` | `hybrid` | 30/30 | 73.3% | 93.3% | 93.3% | 1.214 | 791.2 ms | 0 |

## Misses

- `raw_question` / `bm25`: searchq_v1_003, searchq_v1_013, searchq_v1_014, searchq_v1_020, searchq_v1_022, searchq_v1_025, searchq_v1_026
- `raw_question` / `hybrid`: searchq_v1_003, searchq_v1_010, searchq_v1_020
- `model_rewrite` / `bm25`: searchq_v1_014, searchq_v1_022, searchq_v1_026
- `model_rewrite` / `hybrid`: searchq_v1_022
- `guided_model_rewrite` / `bm25`: searchq_v1_010, searchq_v1_020
- `guided_model_rewrite` / `hybrid`: searchq_v1_010, searchq_v1_020

## Interpretation boundary

Prompts and the corpus guide may be revised using these exposed development cases, with every revision versioned. No method should be promoted until the frozen finalists are evaluated on the independently reviewed holdout.
