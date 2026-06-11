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

- Scored runs: 14 / 14
- Missing runs: 0

## Metrics

- Search decision accuracy: 100.0%
- False search rate: 0.0%
- Missed search rate: 0.0%
- Intent match on expected-search cases: 70.0%
- Layer exact match on expected-search cases: 70.0%
- Average layer recall on expected-search cases: 0.850
- Average focus-term recall on expected-search cases: 0.410
- Correct no-search controls: 100.0%

## Interpretation

- The search/no-search boundary is clean on this seed set.
- Source-need precision is still partial; inspect intent and layer misses before treating retrieval-backend comparisons as meaningful.
- Focus-term recall is low enough that the metric should be treated as a development signal, not a production-quality semantic score.

## Case Table

| Case | Split | Expected Search | Actual Search | Intent Match | Layer Recall | Focus Recall | Status | Failure Reasons |
|---|---|---:|---:|---:|---:|---:|---|---|
| `sourceneed_v1_001` | `dev` | true | true | true | 1.000 | 0.600 | `scored` | - |
| `sourceneed_v1_002` | `dev` | true | true | true | 1.000 | 0.500 | `scored` | - |
| `sourceneed_v1_003` | `dev` | true | true | false | 1.000 | 0.400 | `scored` | - |
| `sourceneed_v1_004` | `scenario_holdout` | true | true | true | 1.000 | 0.600 | `scored` | - |
| `sourceneed_v1_005` | `dev` | true | true | true | 1.000 | 0.250 | `scored` | - |
| `sourceneed_v1_006` | `dev` | true | true | false | 1.000 | 0.750 | `scored` | - |
| `sourceneed_v1_007` | `dev` | true | true | true | 0.000 | 0.200 | `scored` | - |
| `sourceneed_v1_008` | `dev` | true | true | false | 0.500 | 0.400 | `scored` | - |
| `sourceneed_v1_009` | `dev` | true | true | true | 1.000 | 0.400 | `scored` | - |
| `sourceneed_v1_010` | `dev` | true | true | true | 1.000 | 0.000 | `scored` | - |
| `sourceneed_v1_011` | `dev` | false | false | true | 1.000 | 1.000 | `scored` | - |
| `sourceneed_v1_012` | `dev` | false | false | true | 1.000 | 1.000 | `scored` | - |
| `sourceneed_v1_013` | `scenario_holdout` | false | false | true | 1.000 | 1.000 | `scored` | - |
| `sourceneed_v1_014` | `scenario_holdout` | false | false | true | 1.000 | 1.000 | `scored` | - |

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
