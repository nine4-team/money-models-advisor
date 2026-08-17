# Codex Harness Model Routing Eval

## Scope

This report replaces the prior API-replay model-tiering result for advisor-agent planning tasks. The prior API harness inlined business state and asked hosted chat models for bounded JSON; that was useful as a provider experiment, but it was not the product harness. This run uses `codex exec`: the model acts as a Codex agent, can run the local Money Model Advisor CLI, and must write the same trace artifacts scored by the existing golden-dataset scorers.

The current ChatGPT subscription accepts `gpt-5.4-mini` through the Codex CLI in this environment. Earlier attempts to run `gpt-5-mini` through Codex failed because that model was not supported for Codex with this ChatGPT account. This report is therefore a same-harness `gpt-5.4-mini` Codex CLI datapoint, not an API replay.

## Quality

### source_need (14 cases)

| Condition | Strict Case Pass | Search Decision | Subject Exact | Focus Concept Recall |
|---|---:|---:|---:|---:|
| `gpt-5.4-mini` via Codex CLI | 92.9% | 100.0% | 90.0% | 0.745 |
| recorded acting agent reference | 28.6% | 100.0% | 0.0% | - |

### tool_use (24 cases)

| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` via Codex CLI | 75.0% | 0.882 | 0.0% | 0.0% | 16.7% |
| recorded acting agent reference | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |

## Runtime

Token counts are the `tokens used` values printed by Codex CLI, not provider billing records. Because this is a ChatGPT subscription harness, dollar cost is not computed per request.

| Model | Suite | p50 Latency | p95 Latency | Total Reported Tokens | Avg Reported Tokens | Execution Errors |
|---|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` | `source_need` | 39120 ms | 79641 ms | 322282 | 23020.1 | 0 |
| `gpt-5.4-mini` | `tool_use` | 110162 ms | 212735 ms | 925574 | 38565.6 | 0 |

## Failure Modes

- `gpt-5.4-mini` via Codex CLI / `source_need`: `subject_mismatch` x1
- `gpt-5.4-mini` via Codex CLI / `tool_use`: `missing_required:search_source_material` x4, `missed_search` x4, `missing_required:clarify` x1, `missing_required:diagnose` x1
- recorded acting agent reference / `source_need`: `missing_valid_subjects` x10, `search_true_but_no_valid_source_need` x10
- recorded acting agent reference / `tool_use`: none

## Interpretation

The corrected conclusion is narrower and cleaner than the API replay: the project has a Codex-CLI baseline for OpenAI agent execution, and it should not claim that API-tier results decide product routing. Model routing remains a JD-aligned workstream, but future downgrade tests must use a supported Codex model/profile or a deliberately separate provider-API experiment labeled as such.

After resuming the original K1 `tool_use` run, all 24 cases now have full workflow traces and zero execution errors. `gpt-5.4-mini` is promising for source-need classification/generation and repeatably lands at 75.0% strict pass on the tool-use suite, but the remaining misses cluster around required source-search, clarify, and diagnose actions. The practical v1 routing policy remains: deterministic calculations, persistence, retrieval execution, and trace recording stay inside the CLI; semantic planning stays with the agent tier proven through the Codex harness; cheaper tiers need stronger evidence before promotion for broad multi-action planning.

## Per-Case Failures

| Model | Suite | Case | Failure Reasons |
|---|---|---|---|
| `gpt-5.4-mini` | `source_need` | `sourceneed_v1_008` | subject_mismatch |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_002` | missing_required:clarify |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_009` | missing_required:search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_010` | missing_required:search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_019` | missing_required:search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
