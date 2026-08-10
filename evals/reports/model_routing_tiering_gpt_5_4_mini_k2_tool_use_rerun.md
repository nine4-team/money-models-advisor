# Codex Harness Model Routing Eval

## Scope

This report replaces the prior API-replay model-tiering result for advisor-agent planning tasks. The prior API harness inlined business state and asked hosted chat models for bounded JSON; that was useful as a provider experiment, but it was not the product harness. This run uses `codex exec`: the model acts as a Codex agent, can run the local Money Model Advisor CLI, and must write the same trace artifacts scored by the existing golden-dataset scorers.

The current ChatGPT subscription accepts `gpt-5.4-mini` through the Codex CLI in this environment. Earlier attempts to run `gpt-5-mini` through Codex failed because that model was not supported for Codex with this ChatGPT account. This report is therefore a same-harness `gpt-5.4-mini` retry for the `tool_use` suite, not an API replay.

## Quality

### tool_use (24 cases)

| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` via Codex CLI | 75.0% | 0.868 | 0.0% | 0.0% | 12.5% |
| recorded acting agent reference | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |

## Runtime

Token counts are the `tokens used` values printed by Codex CLI, not provider billing records. Because this is a ChatGPT subscription harness, dollar cost is not computed per request.

| Model | Suite | p50 Latency | p95 Latency | Total Reported Tokens | Avg Reported Tokens | Execution Errors |
|---|---|---:|---:|---:|---:|---:|
| `gpt-5.4-mini` | `tool_use` | 123542 ms | 301109 ms | 1244334 | 51847.2 | 0 |

## Failure Modes

- `gpt-5.4-mini` via Codex CLI / `tool_use`: `missing_required:search_source_material` x3, `missed_search` x3, `missing_required:diagnose` x2, `missing_required:inspect_local_docs` x1
- recorded acting agent reference / `tool_use`: none

## Interpretation

The corrected conclusion is narrower and cleaner than the API replay: the project has a Codex-CLI baseline for OpenAI agent execution, and it should not claim that API-tier results decide product routing. Model routing remains a JD-aligned workstream, but future downgrade tests must use a supported Codex model/profile or a deliberately separate provider-API experiment labeled as such.

The practical v1 routing policy remains: deterministic calculations, persistence, retrieval execution, and trace recording stay inside the CLI; semantic planning stays with the agent tier proven through the Codex harness; cheaper tiers are not promoted until they pass the same CLI-backed golden suite.

## Per-Case Failures

| Model | Suite | Case | Failure Reasons |
|---|---|---|---|
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_006` | missing_required:inspect_local_docs |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_008` | missing_required:diagnose |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_009` | missing_required:search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_010` | missing_required:search_source_material, missed_search |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5.4-mini` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
