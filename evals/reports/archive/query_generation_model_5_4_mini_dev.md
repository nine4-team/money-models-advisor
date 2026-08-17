# Query Generation Method Comparison

**Created:** 2026-08-12T01:53:59Z
**Dataset:** `evals/advisor_search_query_cases_enriched_labels.jsonl` (30 exposed development cases)
**Generation model:** `gpt-5.4-mini` for model-driven conditions
**Method version:** `single-query-methods.v1, single-query-methods.v2`

This is development evidence, not the reserved holdout decision. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `model_rewrite` | 30/30 | 8038.4 ms | 7272.5 ms | 97651 |
| `guided_model_rewrite_v2` | 30/30 | 9067.4 ms | 8625.5 ms | 174240 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `model_rewrite` | `bm25` | 30/30 | 60.0% | 86.7% | 93.3% | 52.7% | 47.3% | 1.5 | 93.3 ms | 0 |
| `model_rewrite` | `hybrid` | 30/30 | 66.7% | 96.7% | 100.0% | 56.0% | 44.0% | 1.433 | 890.1 ms | 0 |
| `guided_model_rewrite_v2` | `bm25` | 30/30 | 83.3% | 96.7% | 100.0% | 73.3% | 26.7% | 1.333 | 91.5 ms | 0 |
| `guided_model_rewrite_v2` | `hybrid` | 30/30 | 86.7% | 100.0% | 100.0% | 68.0% | 32.0% | 1.133 | 896.9 ms | 0 |

## Misses

- `model_rewrite` / `bm25`: searchq_v1_010, searchq_v1_022
- `model_rewrite` / `hybrid`: none
- `guided_model_rewrite_v2` / `bm25`: none
- `guided_model_rewrite_v2` / `hybrid`: none

## Interpretation boundary

Prompts and the corpus guide may be revised using these exposed development cases, with every revision versioned. Final selection should be checked on reserved cases.
