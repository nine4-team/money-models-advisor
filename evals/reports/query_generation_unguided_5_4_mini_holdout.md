# Query Generation Method Comparison

**Created:** 2026-08-12T02:03:22Z
**Dataset:** `evals/query_generation/query_generation_holdout_v1.jsonl` (16 regression expansion cases)
**Generation model:** `gpt-5.4-mini` for model-driven conditions
**Method version:** `single-query-methods.v1`

This frozen slice is now part of the shared regression suite. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `model_rewrite` | 16/16 | 8736.0 ms | 8091.6 ms | 66391 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `model_rewrite` | `bm25` | 16/16 | 50.0% | 68.8% | 81.2% | 46.2% | 53.8% | 1.692 | 94.0 ms | 0 |
| `model_rewrite` | `hybrid` | 16/16 | 68.8% | 81.2% | 87.5% | 53.8% | 46.2% | 1.5 | 926.2 ms | 0 |

## Misses

- `model_rewrite` / `bm25`: querygen_holdout_v1_005, querygen_holdout_v1_015, querygen_holdout_v1_016
- `model_rewrite` / `hybrid`: querygen_holdout_v1_005, querygen_holdout_v1_016

## Interpretation boundary

These cases are known and reviewed regression evidence, not an unopened holdout. Future changes should be checked across the complete shared suite.
