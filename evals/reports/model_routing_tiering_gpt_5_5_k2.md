# Codex Harness Model Routing Eval

## Scope

This report replaces the prior API-replay model-tiering result for advisor-agent planning tasks. The prior API harness inlined business state and asked hosted chat models for bounded JSON; that was useful as a provider experiment, but it was not the product harness. This run uses `codex exec`: the model acts as a Codex agent, can run the local Money Model Advisor CLI, and must write the same trace artifacts scored by the existing golden-dataset scorers.

The current ChatGPT subscription exposes `gpt-5.5` as the supported OpenAI Codex model in this environment. Attempts to run `gpt-5-mini` through Codex failed because that model is not supported for Codex with this ChatGPT account. That means this report is a same-harness OpenAI Codex baseline, not a completed multi-tier downgrade decision.

## Quality

### source_need (14 cases)

| Condition | Strict Case Pass | Search Decision | Subject Exact | Focus Concept Recall |
|---|---:|---:|---:|---:|
| `gpt-5.5` via Codex CLI | 92.9% | 100.0% | 90.0% | 0.770 |
| recorded acting agent reference | 28.6% | 100.0% | 0.0% | - |

### tool_use (24 cases)

| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|
| `gpt-5.5` via Codex CLI | 87.5% | 0.965 | 8.3% | 8.3% | 0.0% |
| recorded acting agent reference | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |

## Runtime

Token counts are the `tokens used` values printed by Codex CLI, not provider billing records. Because this is a ChatGPT subscription harness, dollar cost is not computed per request.

| Model | Suite | p50 Latency | p95 Latency | Total Reported Tokens | Avg Reported Tokens | Execution Errors |
|---|---|---:|---:|---:|---:|---:|
| `gpt-5.5` | `source_need` | 34583 ms | 50080 ms | 359232 | 25659.4 | 0 |
| `gpt-5.5` | `tool_use` | 60772 ms | 94837 ms | 703942 | 29330.9 | 0 |

## Failure Modes

- `gpt-5.5` via Codex CLI / `source_need`: `subject_mismatch` x1
- `gpt-5.5` via Codex CLI / `tool_use`: `missing_required:diagnose` x2, `forbidden_action:search_source_material` x2, `false_search` x2
- recorded acting agent reference / `source_need`: `missing_valid_subjects` x10, `search_true_but_no_valid_source_need` x10
- recorded acting agent reference / `tool_use`: none

## Interpretation

The corrected conclusion is narrower and cleaner than the API replay: the project has a Codex-CLI baseline for OpenAI agent execution, and it should not claim that API-tier results decide product routing. Model routing remains a JD-aligned workstream, but future downgrade tests must use a supported Codex model/profile or a deliberately separate provider-API experiment labeled as such.

The practical v1 routing policy remains: deterministic calculations, persistence, retrieval execution, and trace recording stay inside the CLI; semantic planning stays with the agent tier proven through the Codex harness; cheaper tiers are not promoted until they pass the same CLI-backed golden suite.

## Per-Case Failures

| Model | Suite | Case | Failure Reasons |
|---|---|---|---|
| `gpt-5.5` | `source_need` | `sourceneed_v1_008` | subject_mismatch |
| `gpt-5.5` | `tool_use` | `tooluse_v1_008` | missing_required:diagnose |
| `gpt-5.5` | `tool_use` | `tooluse_v1_018` | forbidden_action:search_source_material, false_search |
| `gpt-5.5` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose, forbidden_action:search_source_material, false_search |
