# Advisor Source-Event Trace Eval

## Scope

This eval checks completed advisor-turn traces. It verifies that when one answer needs multiple retrieval jobs, the recorded turn contains multiple source events with distinct SourceNeeds.

It does not run an agent and does not call external model services. Acting agents complete traces separately; this scorer validates the resulting `run.json` artifacts.

## Dataset

- Cases: 1
- Splits: {'post_hardening_regression': 1}

## Validation

- Status: passed

## Run Coverage

- Scored runs: 1 / 1
- Missing runs: 0

## Metrics

- Case pass rate: 100.0%
- Expected source events matched: 2 / 2

## Case Table

| Case | Split | Expected Events | Actual Events | Matched Events | Status | Failure Reasons |
|---|---|---:|---:|---:|---|---|
| `sourceevents_v1_001` | `post_hardening_regression` | 2 | 3 | 2 | `passed` | extra_events:1 |

## Decision

Use this eval to validate post-hardening acting-agent traces before claiming that the advisor reliably handles multi-search answers.
