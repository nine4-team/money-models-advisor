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

This is a partial trace set: 19 of 24 cases have completed `run.json` artifacts.

- Scored by split: {'dev': {'total': 14, 'scored': 14}, 'regression': {'total': 5, 'scored': 5}, 'scenario_holdout': {'total': 5, 'scored': 0}}

Trace-capture note: these artifacts are auditable workflow traces, not a contamination-free blind benchmark. Use them to validate the recorder, evidence shape, and dev/regression policy conformance; use `scenario_holdout` only after guidance is stable.

- Scored cases: 19
- First-action accuracy: 100.0%
- Average required-action recall: 1.000
- Full-sequence pass rate: 100.0%
- Forbidden-action violation rate: 0.0%
- False-search rate: 0.0%
- Missed-search rate: 0.0%
- Trace completeness: 100.0%

## Case Table

| Case | Split | Turn Type | Status | Actual Actions | Failures |
|---|---|---|---|---|---|
| `tooluse_v1_001` | `dev` | `saved_fact_lookup` | scored (evals/runs/next_action/pilot/tooluse_v1_001/run.json) | read_snapshot, read_logs, compose_answer_from_state | - |
| `tooluse_v1_002` | `dev` | `missing_fact_clarification` | scored (evals/runs/next_action/baseline/tooluse_v1_002/run.json) | read_snapshot, clarify | - |
| `tooluse_v1_003` | `dev` | `business_fact_update` | scored (evals/runs/next_action/pilot/tooluse_v1_003/run.json) | update_snapshot, compose_answer_from_state | - |
| `tooluse_v1_004` | `dev` | `business_fact_update` | scored (evals/runs/next_action/baseline/tooluse_v1_004/run.json) | update_snapshot, calculate, compose_answer_from_state | - |
| `tooluse_v1_005` | `dev` | `local_doc_lookup` | scored (evals/runs/next_action/pilot/tooluse_v1_005/run.json) | inspect_local_docs, update_snapshot, compose_answer_from_state | - |
| `tooluse_v1_006` | `dev` | `local_doc_lookup` | scored (evals/runs/next_action/baseline/tooluse_v1_006/run.json) | inspect_local_docs, update_snapshot, compose_answer_from_state | - |
| `tooluse_v1_007` | `dev` | `calculation` | scored (evals/runs/next_action/pilot/tooluse_v1_007/run.json) | read_snapshot, calculate, compose_answer_from_state | - |
| `tooluse_v1_008` | `dev` | `diagnosis` | scored (evals/runs/next_action/baseline/tooluse_v1_008/run.json) | read_snapshot, calculate, diagnose, compose_answer_from_state | - |
| `tooluse_v1_009` | `dev` | `source_required_concept` | scored (evals/runs/next_action/pilot/tooluse_v1_009/run.json) | read_snapshot, search_source_material, compose_answer_from_state | - |
| `tooluse_v1_010` | `dev` | `source_required_recommendation` | scored (evals/runs/next_action/baseline/tooluse_v1_010/run.json) | read_snapshot, calculate, read_logs, search_source_material, compose_answer_from_state | - |
| `tooluse_v1_011` | `dev` | `compose_from_state` | scored (evals/runs/next_action/baseline/tooluse_v1_011/run.json) | read_snapshot, compose_answer_from_state | - |
| `tooluse_v1_012` | `dev` | `simple_definition` | scored (evals/runs/next_action/baseline/tooluse_v1_012/run.json) | answer_without_tool | - |
| `tooluse_v1_013` | `dev` | `read_logs` | scored (evals/runs/next_action/baseline/tooluse_v1_013/run.json) | read_logs, compose_answer_from_state | - |
| `tooluse_v1_014` | `dev` | `clarify` | scored (evals/runs/next_action/baseline/tooluse_v1_014/run.json) | clarify | - |
| `tooluse_v1_015` | `regression` | `saved_fact_lookup_after_diagnosable` | scored (evals/runs/next_action/baseline/tooluse_v1_015/run.json) | read_snapshot, read_logs, compose_answer_from_state | - |
| `tooluse_v1_016` | `regression` | `calculation_after_diagnosable` | scored (evals/runs/next_action/baseline/tooluse_v1_016/run.json) | read_snapshot, calculate, compose_answer_from_state | - |
| `tooluse_v1_017` | `regression` | `compose_after_diagnosable` | scored (evals/runs/next_action/baseline/tooluse_v1_017/run.json) | read_snapshot, compose_answer_from_state | - |
| `tooluse_v1_018` | `regression` | `local_doc_lookup_after_diagnosable` | scored (evals/runs/next_action/baseline/tooluse_v1_018/run.json) | inspect_local_docs, update_snapshot, compose_answer_from_state | - |
| `tooluse_v1_019` | `regression` | `source_required_after_diagnosable` | scored (evals/runs/next_action/baseline/tooluse_v1_019/run.json) | read_snapshot, search_source_material, compose_answer_from_state | - |
| `tooluse_v1_020` | `scenario_holdout` | `simple_definition` | not_run | - | - |
| `tooluse_v1_021` | `scenario_holdout` | `diagnosis` | not_run | - | - |
| `tooluse_v1_022` | `scenario_holdout` | `source_required_compare` | not_run | - | - |
| `tooluse_v1_023` | `scenario_holdout` | `read_logs` | not_run | - | - |
| `tooluse_v1_024` | `scenario_holdout` | `clarify` | not_run | - | - |

## Decision

Use these results as the completed dev/regression trace set. The scenario_holdout split remains intentionally untouched.

## Failure Analysis

No scored dev/regression trace failures were detected.

## Next Experiment

Use dev/regression findings for any guidance changes. Run `scenario_holdout` only after deciding the guidance is stable.
