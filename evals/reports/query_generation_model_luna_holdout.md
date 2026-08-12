# Query Generation Method Comparison

**Created:** 2026-08-10T22:33:05Z
**Dataset:** `evals/query_generation/query_generation_holdout_v1.jsonl` (16 reserved holdout cases)
**Generation model:** `gpt-5.6-luna` for model-driven conditions
**Method version:** `single-query-methods.v2`

All queries and retrieval results were frozen before a method-neutral semantic audit of the shared relevance labels. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `guided_model_rewrite_v2` | 16/16 | 7605.3 ms | 7429.9 ms | 171521 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `guided_model_rewrite_v2` | `hybrid` | 16/16 | 87.5% | 100.0% | 100.0% | 1.25 | 855.9 ms | 0 |

## Misses

- `guided_model_rewrite_v2` / `hybrid`: none

## Interpretation boundary

The post-run audit corrected both omitted relevant passages and overly broad prior labels without changing any query or retrieval result. Because that audit was performed by Codex rather than an independent human reviewer, this is reviewed holdout evidence, not an independently human-adjudicated benchmark.
