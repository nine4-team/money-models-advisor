# gpt-5.4-mini K=3 Codex Harness Aggregate

## Scope

This report aggregates three clean `gpt-5.4-mini` Codex CLI harness passes of the
two model-routing golden suites (14 `source_need` cases, 24 `tool_use` cases). All
runs used `codex exec`, not `OPENAI_API_KEY`, and wrote the same trace artifacts
under `evals/runs/` that a normal advisor turn produces, scored by the same
`score_source_need` / `score_tool_use` scorers used for every other model.

**History note.** Earlier drafts of this report described K1 as "directional only"
and the K2/K3 `tool_use` suites as usage-limit contaminated. That was true of the
first attempt: K1 `tool_use` had 6 cases throttled to empty at startup ("You've hit
your usage limit"), and the original K2/K3 `tool_use` passes had 20 and 19 such
cases. Those throttled cases produced stunted `run.json` files with no
`workflow_steps` and were scored as `missing_actual_actions` failures, which
depressed the reported strict pass. After a ChatGPT account upgrade and a harness
patch that aborts cleanly on quota/auth failures, all three `tool_use` passes were
re-run with zero execution errors. The numbers below are the clean runs.

## Runs

| Run | Report | Summary |
|---|---|---|
| K1 | `evals/reports/model_routing_tiering_gpt_5_4_mini.md` | `evals/reports/model_routing_tiering_gpt_5_4_mini_summary.json` |
| K2 | `evals/reports/model_routing_tiering_gpt_5_4_mini_k2.md` | `evals/reports/model_routing_tiering_gpt_5_4_mini_k2_summary.json` |
| K3 | `evals/reports/model_routing_tiering_gpt_5_4_mini_k3.md` | `evals/reports/model_routing_tiering_gpt_5_4_mini_k3_summary.json` |
| K2 tool-use rerun (clean) | `evals/reports/model_routing_tiering_gpt_5_4_mini_k2_tool_use_rerun.md` | `evals/reports/model_routing_tiering_gpt_5_4_mini_k2_tool_use_rerun_summary.json` |
| K3 tool-use resume (clean) | `evals/reports/model_routing_tiering_gpt_5_4_mini_k3_tool_use_resume.md` | `evals/reports/model_routing_tiering_gpt_5_4_mini_k3_tool_use_resume_summary.json` |

## Source-Need K=3 (clean)

| Run | Strict Case Pass | Search Decision | Subject Exact | Focus Recall | Tokens / Case | p50 Latency | Execution Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| K1 | 92.9% | 100.0% | 90.0% | 0.745 | 23.0k | 39.1 s | 0 |
| K2 | 92.9% | 92.9% | 100.0% | 0.810 | 25.9k | 48.4 s | 0 |
| K3 | 85.7% | 92.9% | 90.0% | 0.755 | 21.2k | 50.0 s | 0 |
| **Mean** | **90.5%** | 95.2% | 93.3% | 0.770 | 23.4k | 45.8 s | 0 |

## Tool-Use K=3 (clean)

| Run | Strict Case Pass | Required Recall | Tokens / Case | p50 Latency | Execution Errors |
|---|---:|---:|---:|---:|---:|
| K1 (re-run clean) | 75.0% | 0.882 | 38.6k | 110.2 s | 0 |
| K2 rerun | 75.0% | 0.868 | 51.8k | 123.5 s | 0 |
| K3 resume | 75.0% | 0.889 | 42.7k | 102.0 s | 0 |
| **Mean** | **75.0%** | 0.880 | 44.4k | 111.9 s | 0 |

Tool-use strict pass is 75.0% on all three clean runs. The remaining misses are
scored model behavior, not infrastructure: across runs they cluster on missed
source-material searches and missed diagnose actions, with zero forbidden-action or
false-search violations.

## Interpretation

`gpt-5.4-mini` is a strong candidate for the light **source-need** routing decision:
across three passes it averaged 90.5% strict case pass (92.9 / 92.9 / 85.7), on par
with the best tier measured on that suite, at ~23k Codex-reported tokens per case.

For broad **tool-use** orchestration it is materially weaker but stable: 75.0% strict
pass on every clean run, held back by missed required searches and diagnoses. That is
below a promotion bar for the full multi-step planning role without stronger prompting
or added routing constraints, but it is a genuine, repeatable result — not the earlier
throttle artifact.
