# Advisor Source-Event Trace Eval

## Scope

This eval checks completed advisor-turn traces. It verifies that source-backed answers contain the expected source events, multi-job answers split retrieval into distinct SourceNeeds, and no-search turns do not fabricate source events.

It does not run an agent and does not call external model services. Acting agents complete traces separately; this scorer validates the resulting `run.json` artifacts.

## Trace Requirement

- Query variants required: no
- Query variants must be present in executed queries: no

## Dataset

- Cases: 6
- Splits: {'post_hardening_regression': 6}

## Validation

- Status: passed

## Run Coverage

- Scored runs: 6 / 6
- Missing runs: 0

## Metrics

- Case pass rate: 16.7%
- Expected source events matched: 0 / 6
- Extra source-event warnings: 5 cases / 6 events

## Case Table

| Case | Split | Expected Events | Actual Events | Matched Events | Status | Findings |
|---|---|---:|---:|---:|---|---|
| `sourceevents_v1_001` | `post_hardening_regression` | 2 | 2 | 0 | `failed` | missing_intent:diagnostic_evidence, subject_miss:diagnostic_evidence, focus_miss:diagnostic_evidence, missing_chunks:diagnostic_evidence, missing_intent:recommendation_evidence, subject_miss:recommendation_evidence, focus_miss:recommendation_evidence, missing_chunks:recommendation_evidence, extra_events:2 |
| `sourceevents_v1_002` | `post_hardening_regression` | 1 | 1 | 0 | `failed` | missing_intent:diagnostic_evidence, subject_miss:diagnostic_evidence, focus_miss:diagnostic_evidence, missing_chunks:diagnostic_evidence, extra_events:1 |
| `sourceevents_v1_003` | `post_hardening_regression` | 1 | 1 | 0 | `failed` | missing_intent:recommendation_evidence, subject_miss:recommendation_evidence, focus_miss:recommendation_evidence, missing_chunks:recommendation_evidence, extra_events:1 |
| `sourceevents_v1_004` | `post_hardening_regression` | 0 | 0 | 0 | `passed` | - |
| `sourceevents_v1_005` | `post_hardening_regression` | 1 | 1 | 0 | `failed` | missing_intent:teaching_evidence, subject_miss:teaching_evidence, focus_miss:teaching_evidence, missing_chunks:teaching_evidence, extra_events:1 |
| `sourceevents_v1_006` | `post_hardening_regression` | 1 | 1 | 0 | `failed` | missing_intent:recommendation_evidence, subject_miss:recommendation_evidence, focus_miss:recommendation_evidence, missing_chunks:recommendation_evidence, extra_events:1 |

## Decision

Use this eval to validate post-hardening acting-agent traces before claiming that the advisor reliably decides when to search, when not to search, and when to split one answer into multiple source-material searches.
