# Advisor Tool-Use Judgment Eval

## Hypothesis

The skill-guided advisor should choose the correct next action or action sequence before answering: read saved state, inspect logs, inspect local docs, calculate, diagnose, search source material, clarify, update memory, or answer without tools.

## Dataset Slice

- Cases: 24
- Splits: {'dev': 14, 'regression': 5, 'scenario_holdout': 5}
- Turn types: {'business_fact_update': 2, 'calculation': 1, 'calculation_after_diagnosable': 1, 'clarify': 2, 'compose_after_diagnosable': 1, 'compose_from_state': 1, 'diagnosis': 2, 'local_doc_lookup': 2, 'local_doc_lookup_after_diagnosable': 1, 'missing_fact_clarification': 1, 'read_logs': 2, 'saved_fact_lookup': 1, 'saved_fact_lookup_after_diagnosable': 1, 'simple_definition': 2, 'source_required_after_diagnosable': 1, 'source_required_compare': 1, 'source_required_concept': 1, 'source_required_recommendation': 1}

These are product-behavior cases. Harness/operability questions about eval terminology should live in a separate file and should not count toward headline advisor-quality metrics.

## Validation

- Status: passed

## Metrics

- first-action accuracy
- required-action recall
- forbidden-action violation rate
- false-search rate
- missed-search rate
- full-sequence pass rate
- trace completeness

## Results

No `run.json` artifacts were found, so this report currently covers case inventory and validation only.

Next step: run the skill-guided agent workflow for each case in isolated eval directories and write `run.json` traces under `evals/runs/next_action/`.

## Case Table

| Case | Split | Turn Type | Status | Actual Actions | Failures |
|---|---|---|---|---|---|
| `tooluse_v1_001` | `dev` | `saved_fact_lookup` | not_run | - | - |
| `tooluse_v1_002` | `dev` | `missing_fact_clarification` | not_run | - | - |
| `tooluse_v1_003` | `dev` | `business_fact_update` | not_run | - | - |
| `tooluse_v1_004` | `dev` | `business_fact_update` | not_run | - | - |
| `tooluse_v1_005` | `dev` | `local_doc_lookup` | not_run | - | - |
| `tooluse_v1_006` | `dev` | `local_doc_lookup` | not_run | - | - |
| `tooluse_v1_007` | `dev` | `calculation` | not_run | - | - |
| `tooluse_v1_008` | `dev` | `diagnosis` | not_run | - | - |
| `tooluse_v1_009` | `dev` | `source_required_concept` | not_run | - | - |
| `tooluse_v1_010` | `dev` | `source_required_recommendation` | not_run | - | - |
| `tooluse_v1_011` | `dev` | `compose_from_state` | not_run | - | - |
| `tooluse_v1_012` | `dev` | `simple_definition` | not_run | - | - |
| `tooluse_v1_013` | `dev` | `read_logs` | not_run | - | - |
| `tooluse_v1_014` | `dev` | `clarify` | not_run | - | - |
| `tooluse_v1_015` | `regression` | `saved_fact_lookup_after_diagnosable` | not_run | - | - |
| `tooluse_v1_016` | `regression` | `calculation_after_diagnosable` | not_run | - | - |
| `tooluse_v1_017` | `regression` | `compose_after_diagnosable` | not_run | - | - |
| `tooluse_v1_018` | `regression` | `local_doc_lookup_after_diagnosable` | not_run | - | - |
| `tooluse_v1_019` | `regression` | `source_required_after_diagnosable` | not_run | - | - |
| `tooluse_v1_020` | `scenario_holdout` | `simple_definition` | not_run | - | - |
| `tooluse_v1_021` | `scenario_holdout` | `diagnosis` | not_run | - | - |
| `tooluse_v1_022` | `scenario_holdout` | `source_required_compare` | not_run | - | - |
| `tooluse_v1_023` | `scenario_holdout` | `read_logs` | not_run | - | - |
| `tooluse_v1_024` | `scenario_holdout` | `clarify` | not_run | - | - |

## Decision

Use this report as the next-action classification backbone. It is ready to score captured traces, but it should not be presented as behavior results until run artifacts exist.

## Failure Analysis

Failure analysis is deferred until scored traces exist.

## Next Experiment

Build or capture isolated `run.json` traces for the current cases, then use this scorer to generate baseline metrics before changing the skill/tool guidance.
