# Model Routing And Tiering Eval

## Scope

This experiment replays two golden suites as single bounded JSON completions across hosted model tiers, then scores every condition with the existing deterministic scorers. The suites are `source_need` (search/no-search decision plus structured SourceNeed) and `tool_use` (ordered next-action sequence from the fixed taxonomy). These two were chosen because the model task is one validated completion, so the comparison isolates model judgment from harness differences.

This is the explicit model-comparison experiment allowed by `JD_REQUIREMENTS_AUDIT.md`. Raw prompts and responses are recorded under `evals/runs/model_routing/` for audit. Sampling uses provider defaults; gpt-5-family models run with default reasoning effort, which is part of what the latency column measures.

The recorded interactive acting-agent condition (Claude operating the CLI in captured trace sessions) is scored with the same scorers as a reference row. It had CLI access, real state inspection, and multi-step iteration, so treat its quality as a different-harness reference, not a same-task competitor; its latency and cost are not comparable and are omitted.

## Quality

Strict case pass means: search/no-search decision correct, and on expected-search cases intent match plus exact layer match (`source_need`); or required-action recall 1.0 with no forbidden actions and a complete trace (`tool_use`).

### source_need (14 cases)

| Condition | Strict Case Pass | Search Decision | Intent Match | Layer Exact | Focus Concept Recall |
|---|---:|---:|---:|---:|---:|
| `gpt-5` | 71.4% | 100.0% | 70.0% | 90.0% | 0.690 |
| `gpt-5-mini` | 50.0% | 64.3% | 40.0% | 30.0% | 0.660 |
| `gpt-5-nano` | 28.6% | 35.7% | 0.0% | 10.0% | 0.800 |
| `gpt-4.1-mini` | 50.0% | 78.6% | 70.0% | 80.0% | 0.485 |
| recorded acting agent (reference) | 92.9% | 100.0% | 100.0% | 90.0% | 0.750 |

### tool_use (24 cases)

| Condition | Strict Case Pass | First Action | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|---:|
| `gpt-5` | 66.7% | 79.2% | 0.812 | 0.0% | 0.0% | 16.7% |
| `gpt-5-mini` | 70.8% | 79.2% | 0.840 | 0.0% | 0.0% | 16.7% |
| `gpt-5-nano` | 70.8% | 87.5% | 0.854 | 0.0% | 0.0% | 16.7% |
| `gpt-4.1-mini` | 50.0% | 62.5% | 0.632 | 0.0% | 0.0% | 16.7% |
| recorded acting agent (reference) | 100.0% | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |


## Latency And Cost

Latency is wall-clock per completion including provider queue and default reasoning. Cost uses the static June 2026 pricing table in `scripts/eval_model_routing.py`; reasoning tokens bill as completion tokens.

| Model | Suite | p50 Latency | p95 Latency | Prompt Tokens | Completion Tokens | Est. Cost | Est. Cost / Case | Request Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `gpt-5` | `source_need` | 12812 ms | 26401 ms | 18841 | 12732 | $0.1509 | $0.010777 | 0 |
| `gpt-5` | `tool_use` | 12481 ms | 29508 ms | 29559 | 27195 | $0.3089 | $0.012871 | 0 |
| `gpt-5-mini` | `source_need` | 5356 ms | 12223 ms | 18841 | 5968 | $0.0166 | $0.001189 | 0 |
| `gpt-5-mini` | `tool_use` | 7606 ms | 22577 ms | 29559 | 14287 | $0.0360 | $0.001498 | 0 |
| `gpt-5-nano` | `source_need` | 9148 ms | 17024 ms | 18841 | 17271 | $0.0078 | $0.000561 | 0 |
| `gpt-5-nano` | `tool_use` | 14235 ms | 26366 ms | 29559 | 45599 | $0.0197 | $0.000822 | 0 |
| `gpt-4.1-mini` | `source_need` | 1004 ms | 2250 ms | 18855 | 603 | $0.0085 | $0.000608 | 0 |
| `gpt-4.1-mini` | `tool_use` | 1208 ms | 4473 ms | 29583 | 1488 | $0.0142 | $0.000592 | 0 |

## Failure Modes

- `gpt-5` / `source_need`: `intent_mismatch` x3, `layer_mismatch` x1
- `gpt-5` / `tool_use`: `wrong_first_action` x5, `missed_search` x4, `missing_required:calculate` x2, `missing_required:search_source_material` x2, `missing_required:read_snapshot,search_source_material` x1, `missing_required:calculate,search_source_material` x1, `missing_required:diagnose` x1, `missing_required:read_snapshot` x1
- `gpt-5-mini` / `source_need`: `missed_search` x5, `layer_mismatch` x2, `intent_mismatch` x1
- `gpt-5-mini` / `tool_use`: `wrong_first_action` x5, `missed_search` x4, `missing_required:search_source_material` x3, `missing_required:calculate` x1, `missing_required:calculate,diagnose` x1, `missing_required:calculate,search_source_material` x1, `missing_required:diagnose` x1
- `gpt-5-nano` / `source_need`: `missed_search` x9, `intent_mismatch` x1
- `gpt-5-nano` / `tool_use`: `missing_required:search_source_material` x4, `missed_search` x4, `wrong_first_action` x3, `missing_required:calculate` x1, `missing_required:calculate,diagnose` x1, `missing_required:diagnose` x1
- `gpt-4.1-mini` / `source_need`: `intent_mismatch` x3, `false_search` x3, `layer_mismatch` x2
- `gpt-4.1-mini` / `tool_use`: `wrong_first_action` x9, `missing_required:read_snapshot` x4, `missed_search` x4, `actual_actions[0]_not_object` x3, `missing_required:read_snapshot,search_source_material` x2, `missing_required:clarify` x1, `missing_required:calculate` x1, `missing_required:calculate,read_snapshot` x1, `missing_required:calculate,search_source_material` x1, `actual_actions[1]_not_object` x1, `missing_required:search_source_material` x1, `missing_required:answer_without_tool` x1
- recorded acting agent / `source_need`: `layer_mismatch` x1
- recorded acting agent / `tool_use`: none

## Interpretation And Routing Decision

This section interprets the June 2026 full-matrix run (4 OpenAI tiers x 38 cases, 0 request errors). Re-running with different models or cases requires re-authoring it.

1. **No cheaper tier maintains output quality on agent-planning tasks, so nothing routes downward in v1.** The strongest tier tested (`gpt-5`) reaches 71.4% strict pass on `source_need` versus 92.9% for the recorded interactive agent, and every cheaper tier is materially worse. The JD asks for routing that improves unit economics *while maintaining output quality*; on these suites that bar is not met by any tested downgrade, and recording that is the routing decision.

2. **Tier separation is real and directional on `source_need`.** `gpt-5` holds 100% search-decision accuracy. The cheaper reasoning tiers fail closed: `gpt-5-mini` misses 5 of 10 expected searches and `gpt-5-nano` misses 9 of 10, declining clearly search-worthy turns. The non-reasoning `gpt-4.1-mini` fails open instead: 3 false searches on the 4 no-search controls. Failing closed degrades answer citations silently; failing open burns retrieval cost and pollutes answers. Neither failure direction is acceptable as a default.

3. **Model family changes the failure mode, not just the rate.** The gpt-5 reasoning family never violated the output contract; `gpt-4.1-mini` returned malformed action objects on 3 of 24 `tool_use` cases on top of the highest wrong-first-action rate. It is also roughly 10x faster (p50 about 1.0-1.2s versus 5-14s) and 20x cheaper per case than `gpt-5` — a real latency/cost win that the quality column disqualifies for planning tasks, but which would matter for bounded low-stakes transforms.

4. **Cheap-tier reasoning is not free.** `gpt-5-nano` spent 45,599 completion tokens on `tool_use` — more than triple `gpt-5-mini` — for equal-or-worse quality. Token-based pricing keeps it cheapest in dollars, but its p50 latency (about 9-14s) lands near `gpt-5`. Routing decisions should be made on the measured latency/quality pair, not the price sheet alone.

5. **Caveat: the `tool_use` replay is harness-coupled.** Six cases fail across every API tier while the recorded interactive agent passed all of them. Those labels require CLI actions (`read_snapshot`, `calculate`, `search_source_material`) that a bounded completion with state already inlined tends to skip in favor of answering directly. Part of the API-tier gap on `tool_use` therefore measures harness mismatch, not model judgment; `source_need` is the cleaner tier discriminator. The recorded-agent comparison also crosses providers (Claude interactive versus OpenAI bounded), so it is direction-of-evidence, not a controlled provider benchmark.

Routing policy for v1: deterministic work (calculation, diagnosis, retrieval execution, trace recording) stays in the CLI at zero model cost — that is the product's primary unit-economics lever. Agent planning (next action, source need) stays on the strong interactive tier. The first candidates for routed downgrades are bounded low-stakes transforms such as query-variant phrasing, and any downgrade must first match the recorded baseline on the relevant golden suite.

## Per-Case Failures

| Model | Suite | Case | Failure Reasons |
|---|---|---|---|
| `gpt-5` | `source_need` | `sourceneed_v1_003` | intent_mismatch |
| `gpt-5` | `source_need` | `sourceneed_v1_006` | intent_mismatch |
| `gpt-5` | `source_need` | `sourceneed_v1_007` | intent_mismatch |
| `gpt-5` | `source_need` | `sourceneed_v1_008` | layer_mismatch |
| `gpt-5` | `tool_use` | `tooluse_v1_004` | wrong_first_action |
| `gpt-5` | `tool_use` | `tooluse_v1_007` | missing_required:calculate |
| `gpt-5` | `tool_use` | `tooluse_v1_008` | missing_required:calculate |
| `gpt-5` | `tool_use` | `tooluse_v1_009` | wrong_first_action, missing_required:read_snapshot,search_source_material, missed_search |
| `gpt-5` | `tool_use` | `tooluse_v1_010` | missing_required:calculate,search_source_material, missed_search |
| `gpt-5` | `tool_use` | `tooluse_v1_014` | wrong_first_action |
| `gpt-5` | `tool_use` | `tooluse_v1_019` | missing_required:search_source_material, missed_search |
| `gpt-5` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
| `gpt-5` | `tool_use` | `tooluse_v1_023` | wrong_first_action |
| `gpt-5` | `tool_use` | `tooluse_v1_024` | wrong_first_action, missing_required:read_snapshot |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_002` | layer_mismatch |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_003` | missed_search |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_005` | missed_search |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_006` | missed_search |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_007` | missed_search |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_008` | intent_mismatch, layer_mismatch |
| `gpt-5-mini` | `source_need` | `sourceneed_v1_009` | missed_search |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_005` | wrong_first_action |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_006` | wrong_first_action |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_007` | missing_required:calculate |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_008` | missing_required:calculate,diagnose |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_009` | missing_required:search_source_material, missed_search |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_010` | missing_required:calculate,search_source_material, missed_search |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_014` | wrong_first_action |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_018` | wrong_first_action |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_019` | missing_required:search_source_material, missed_search |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
| `gpt-5-mini` | `tool_use` | `tooluse_v1_023` | wrong_first_action |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_001` | intent_mismatch |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_002` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_003` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_004` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_005` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_006` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_007` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_008` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_009` | missed_search |
| `gpt-5-nano` | `source_need` | `sourceneed_v1_010` | missed_search |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_007` | missing_required:calculate |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_008` | missing_required:calculate,diagnose |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_009` | missing_required:search_source_material, missed_search |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_010` | wrong_first_action, missing_required:search_source_material, missed_search |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_018` | wrong_first_action |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_019` | missing_required:search_source_material, missed_search |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_021` | missing_required:diagnose |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_022` | missing_required:search_source_material, missed_search |
| `gpt-5-nano` | `tool_use` | `tooluse_v1_023` | wrong_first_action |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_001` | intent_mismatch |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_003` | layer_mismatch |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_006` | intent_mismatch |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_008` | intent_mismatch, layer_mismatch |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_011` | false_search |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_012` | false_search |
| `gpt-4.1-mini` | `source_need` | `sourceneed_v1_014` | false_search |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_001` | wrong_first_action, missing_required:read_snapshot |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_002` | missing_required:clarify |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_007` | missing_required:calculate |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_008` | wrong_first_action, missing_required:calculate,read_snapshot |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_009` | wrong_first_action, missing_required:read_snapshot,search_source_material, missed_search |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_010` | missing_required:calculate,search_source_material, missed_search |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_015` | actual_actions[0]_not_object, actual_actions[1]_not_object, wrong_first_action, missing_required:read_snapshot |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_019` | missing_required:search_source_material, missed_search |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_020` | actual_actions[0]_not_object, wrong_first_action, missing_required:answer_without_tool |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_021` | wrong_first_action, missing_required:read_snapshot |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_022` | actual_actions[0]_not_object, wrong_first_action, missing_required:read_snapshot,search_source_material, missed_search |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_023` | wrong_first_action |
| `gpt-4.1-mini` | `tool_use` | `tooluse_v1_024` | wrong_first_action, missing_required:read_snapshot |
