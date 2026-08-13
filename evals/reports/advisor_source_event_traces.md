# Advisor Source-Event Trace Eval

## Scope

This scorer checks completed turns against the active single-query `SearchRequest` contract. It verifies search/no-search restraint, one event per evidence job, required query concepts, exact query execution, and inspected chunk recording.

`intent` must be a valid trace label but is not compared with an answer key because it does not control retrieval.

## Dataset

- Cases: 6
- Splits: {'search_request_v1': 6}

## Validation

- Status: passed

## Run Coverage

- Scored runs: 6 / 6
- Missing runs: 0

## Metrics

- Case pass rate: 100.0%
- Expected source events matched: 7 / 7
- Extra source events: 0

## Case Table

| Case | Expected | Actual | Matched | Status | Findings |
|---|---:|---:|---:|---|---|
| `sourceevents_v1_001` | 3 | 3 | 3 | `passed` | - |
| `sourceevents_v1_002` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_003` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_004` | 0 | 0 | 0 | `passed` | - |
| `sourceevents_v1_005` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_006` | 1 | 1 | 1 | `passed` | - |

## Answer-Key Audit

The run artifacts were frozen before these label corrections; queries and retrieval were not rerun.

- `sourceevents_v1_001`: added one valid source event returned by the frozen blind run. The additional event supported the cited rollout-priority claim and was not redundant with the economics or mechanism evidence.
- `sourceevents_v1_005`: removed an unnecessarily prescriptive query term. The frozen query retrieved directly useful definition evidence; requiring the phrase core offer tested wording rather than retrieval intent.
