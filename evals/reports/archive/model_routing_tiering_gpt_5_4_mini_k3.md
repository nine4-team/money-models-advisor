# Codex Harness Model Routing Eval

## Scope

This report replaces the prior API-replay model-tiering result for advisor-agent planning tasks. The prior API harness inlined business state and asked hosted chat models for bounded JSON; that was useful as a provider experiment, but it was not the product harness. This run uses `codex exec`: the model acts as a Codex agent, can run the local Money Model Advisor CLI, and must write the same trace artifacts scored by the existing golden-dataset scorers.

The current ChatGPT subscription exposes `gpt-5.5` as the supported OpenAI Codex model in this environment. Attempts to run `gpt-5-mini` through Codex failed because that model is not supported for Codex with this ChatGPT account. That means this report is a same-harness OpenAI Codex baseline, not a completed multi-tier downgrade decision.

## Quality

### source_need (14 cases)

| Condition | Strict Case Pass | Search Decision | Subject Exact | Focus Concept Recall |
|---|---:|---:|---:|---:|
| `gpt-5.4-mini` via Codex CLI | 85.7% | 92.9% | 90.0% | 0.755 |
| recorded acting agent reference | 28.6% | 100.0% | 0.0% | - |

### tool_use (24 cases)

| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` via Codex CLI | 12.5% | 0.167 | 0.0% | 0.0% | 16.7% |
| recorded acting agent reference | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |

## Runtime

Token counts are the `tokens used` values printed by Codex CLI, not provider billing records. Because this is a ChatGPT subscription harness, dollar cost is not computed per request.

| Model | Suite | p50 Latency | p95 Latency | Total Reported Tokens | Avg Reported Tokens | Execution Errors |
|---|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` | `source_need` | 49991 ms | 115460 ms | 297199 | 21228.5 | 0 |
| `gpt-5.4-mini` | `tool_use` | 7293 ms | 135158 ms | 266176 | 44362.7 | 19 |

## Failure Modes

- `gpt-5.4-mini` via Codex CLI / `source_need`: `subject_mismatch` x1, `false_search` x1
- `gpt-5.4-mini` via Codex CLI / `tool_use`: `missing_actual_actions` x19, `missed_search` x4, `missing_required:inspect_local_docs` x3, `missing_required:calculate,read_snapshot` x2, `missing_required:read_snapshot,search_source_material` x2, `missing_required:compose_answer_from_state,read_snapshot` x2, `missing_required:answer_without_tool` x2, `missing_required:clarify,read_snapshot` x1, `missing_required:update_snapshot` x1, `missing_required:calculate,update_snapshot` x1, `missing_required:calculate,diagnose,read_snapshot` x1, `missing_required:calculate,read_snapshot,search_source_material` x1, `missing_required:read_logs` x1, `missing_required:clarify` x1, `missing_required:read_snapshot` x1, `missing_required:diagnose` x1, `missing_required:search_source_material` x1
- recorded acting agent reference / `source_need`: `missing_valid_subjects` x10, `search_true_but_no_valid_source_need` x10
- recorded acting agent reference / `tool_use`: none

## Interpretation

The corrected conclusion is narrower and cleaner than the API replay: the project has a Codex-CLI baseline for OpenAI agent execution, and it should not claim that API-tier results decide product routing. Model routing remains a JD-aligned workstream, but future downgrade tests must use a supported Codex model/profile or a deliberately separate provider-API experiment labeled as such.

The practical v1 routing policy remains: deterministic calculations, persistence, retrieval execution, and trace recording stay inside the CLI; semantic planning stays with the agent tier proven through the Codex harness; cheaper tiers are not promoted until they pass the same CLI-backed golden suite.

## Per-Case Failures

| Model | Suite | Case | Failure Reasons |
|---|---|---|---|
| `gpt-5.4-mini` | `source_need` | `sourceneed_v1_008` | subject_mismatch |
| `gpt-5.4-mini` | `source_need` | `sourceneed_v1_011` | false_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_002` | missing_actual_actions, missing_required:clarify,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_003` | missing_actual_actions, missing_required:update_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_004` | missing_actual_actions, missing_required:calculate,update_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_005` | missing_actual_actions, missing_required:inspect_local_docs |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_006` | missing_actual_actions, missing_required:inspect_local_docs |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_007` | missing_actual_actions, missing_required:calculate,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_008` | missing_actual_actions, missing_required:calculate,diagnose,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_009` | missing_actual_actions, missing_required:read_snapshot,search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_010` | missing_actual_actions, missing_required:calculate,read_snapshot,search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_011` | missing_actual_actions, missing_required:compose_answer_from_state,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_012` | missing_actual_actions, missing_required:answer_without_tool |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_013` | missing_actual_actions, missing_required:read_logs |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_014` | missing_actual_actions, missing_required:clarify |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_015` | missing_actual_actions, missing_required:read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_016` | missing_actual_actions, missing_required:calculate,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_017` | missing_actual_actions, missing_required:compose_answer_from_state,read_snapshot |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_018` | missing_actual_actions, missing_required:inspect_local_docs |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_019` | missing_actual_actions, missing_required:read_snapshot,search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_020` | missing_actual_actions, missing_required:answer_without_tool |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
