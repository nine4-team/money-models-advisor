# Advisor Source-Need Generation Eval

## Scope

This eval checks the step between next-action classification and query construction. Given conversation context, snapshot state, and the current user turn, the acting agent should decide whether source-material search is needed and, if it is, generate a structured source need.

A source need contains retrieval intent, corpus layer or layers, and focus terms. The query builder then turns that structure into a concrete search query.

This script does not run an agent and does not call external model services. It validates labels and scores saved `run.json` artifacts when they exist under `evals/runs/source_need/`.

## Dataset

- Cases: 14
- Splits: {'dev': 11, 'scenario_holdout': 3}
- Expected search: {False: 4, True: 10}

## Validation

- Status: passed

## Run Coverage

- Scored runs: 0 / 14
- Missing runs: 14

## Metrics

- Status: inventory only; no source-need run artifacts found yet.

## Case Table

| Case | Split | Expected Search | Actual Search | Intent Match | Layer Recall | Focus Recall | Status | Failure Reasons |
|---|---|---:|---:|---:|---:|---:|---|---|
| `sourceneed_v1_001` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_002` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_003` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_004` | `scenario_holdout` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_005` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_006` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_007` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_008` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_009` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_010` | `dev` | true | - | - | - | - | `not_run` | - |
| `sourceneed_v1_011` | `dev` | false | - | - | - | - | `not_run` | - |
| `sourceneed_v1_012` | `dev` | false | - | - | - | - | `not_run` | - |
| `sourceneed_v1_013` | `scenario_holdout` | false | - | - | - | - | `not_run` | - |
| `sourceneed_v1_014` | `scenario_holdout` | false | - | - | - | - | `not_run` | - |

## Decision

Use this eval before comparing BM25, dense, or hybrid retrieval. If the acting agent chooses the wrong source need, retrieval-backend comparisons will mostly measure upstream planning noise.

## Expected Run Artifact Shape

```json
{
  "case_id": "sourceneed_v1_001",
  "source_search_decision": true,
  "source_need": {
    "intent": "teaching_evidence",
    "layers": [
      "unit-economics"
    ],
    "focus_terms": [
      "gross profit",
      "fulfillment cost",
      "CAC",
      "payback period"
    ]
  }
}
```
