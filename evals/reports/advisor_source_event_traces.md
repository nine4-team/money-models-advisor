# Advisor Source-Event Trace Eval

## Scope

This eval checks completed advisor-turn traces. It verifies that source-backed answers contain the expected source events, multi-job answers split retrieval into distinct SourceNeeds, and no-search turns do not fabricate source events.

It does not run an agent and does not call external model services. Acting agents complete traces separately; this scorer validates the resulting `run.json` artifacts.

## Dataset

- Cases: 6
- Splits: {'post_hardening_regression': 6}

## Validation

- Status: passed

## Run Coverage

- Scored runs: 6 / 6
- Missing runs: 0

## Metrics

- Case pass rate: 100.0%
- Expected source events matched: 6 / 6
- Extra source-event warnings: 0 cases / 0 events

## Case Table

| Case | Split | Expected Events | Actual Events | Matched Events | Status | Findings |
|---|---|---:|---:|---:|---|---|
| `sourceevents_v1_001` | `post_hardening_regression` | 2 | 2 | 2 | `passed` | - |
| `sourceevents_v1_002` | `post_hardening_regression` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_003` | `post_hardening_regression` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_004` | `post_hardening_regression` | 0 | 0 | 0 | `passed` | - |
| `sourceevents_v1_005` | `post_hardening_regression` | 1 | 1 | 1 | `passed` | - |
| `sourceevents_v1_006` | `post_hardening_regression` | 1 | 1 | 1 | `passed` | - |

## Decision

Use this eval to validate post-hardening acting-agent traces before claiming that the advisor reliably decides when to search, when not to search, and when to split one answer into multiple source-material searches.
