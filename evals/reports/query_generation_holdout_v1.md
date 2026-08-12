# Query Generation Method Comparison

**Created:** 2026-08-12T01:53:59Z
**Dataset:** `evals/query_generation/query_generation_holdout_v1.jsonl` (16 regression expansion cases)
**Generation model:** `gpt-5.5` for model-driven conditions
**Method version:** `single-query-methods.v1, single-query-methods.v2`

This frozen slice is now part of the shared regression suite. Every query was retrieved through the public CLI with no subject filter.

## Generation

The `model_rewrite` condition is the unguided condition: it receives the normal saved business snapshot but no additional corpus guide. The guided condition receives the same snapshot plus the versioned guide.

| Method | Valid outputs | Mean latency | p50 latency | Codex-reported tokens |
|---|---:|---:|---:|---:|
| `raw_question` | 16/16 | 0 ms | 0 ms | 0 |
| `model_rewrite` | 16/16 | 5787.8 ms | 5505.4 ms | 123608 |
| `guided_model_rewrite_v2` | 16/16 | 6737.2 ms | 5840.0 ms | 72139 |

## Retrieval

Quality percentages use only completed searches as the denominator. Coverage makes interrupted or missing executions explicit.
Rows with incomplete coverage are descriptive only and must not be compared directly with complete rows.

| Method | Backend | Coverage | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 | Mean first useful rank | Mean retrieval latency | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `raw_question` | `bm25` | 16/16 | 56.2% | 62.5% | 81.2% | 38.8% | 61.2% | 1.846 | 95.8 ms | 0 |
| `raw_question` | `hybrid` | 16/16 | 56.2% | 75.0% | 75.0% | 42.5% | 57.5% | 1.333 | 968.7 ms | 0 |
| `model_rewrite` | `bm25` | 16/16 | 56.2% | 87.5% | 87.5% | 46.2% | 53.8% | 1.429 | 93.0 ms | 0 |
| `model_rewrite` | `hybrid` | 16/16 | 68.8% | 87.5% | 87.5% | 52.5% | 47.5% | 1.357 | 777.6 ms | 0 |
| `guided_model_rewrite_v2` | `bm25` | 16/16 | 87.5% | 93.8% | 100.0% | 76.2% | 23.8% | 1.375 | 92.9 ms | 0 |
| `guided_model_rewrite_v2` | `hybrid` | 16/16 | 100.0% | 100.0% | 100.0% | 82.5% | 17.5% | 1.0 | 739.5 ms | 0 |

## Misses

- `raw_question` / `bm25`: querygen_holdout_v1_004, querygen_holdout_v1_005, querygen_holdout_v1_015
- `raw_question` / `hybrid`: querygen_holdout_v1_004, querygen_holdout_v1_005, querygen_holdout_v1_014, querygen_holdout_v1_016
- `model_rewrite` / `bm25`: querygen_holdout_v1_005, querygen_holdout_v1_015
- `model_rewrite` / `hybrid`: querygen_holdout_v1_005, querygen_holdout_v1_013
- `guided_model_rewrite_v2` / `bm25`: none
- `guided_model_rewrite_v2` / `hybrid`: none

## Interpretation boundary

These cases are known and reviewed regression evidence, not an unopened holdout. Future changes should be checked across the complete shared suite.
