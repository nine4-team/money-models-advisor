# Opus Harness Model Routing Eval

## Scope

This report runs the same two model-routing golden suites used for the gpt-5.5 Codex
baseline (`evals/reports/model_routing_tiering.md`), but with **Claude Opus 4.8 as the
acting agent** instead of an OpenAI Codex agent. It gives the project a second-provider
data point for the JD's "worked across multiple LLM providers" and "model routing"
requirements.

The harness is held as close to the gpt-5.5 run as possible:

- The case directories and acting prompts are produced by the exact same prep code
  (`scripts/eval_codex_model_routing.py::run_prepare`), so the prompt text, the
  hidden-label stripping, and the appended noninteractive completion requirement are
  byte-identical to what gpt-5.5 received.
- Opus acted on each case in its own isolated context (one subagent per case), reading
  only the prepared `acting_prompt.md`, the operating skill, and the case's own saved
  state via the local CLI. Expected labels were never read.
- The same scorers (`score_source_need`, `score_tool_use`) score the resulting
  `run.json` artifacts, and the recorded acting-agent reference column is computed from
  the same recorded runs as the gpt-5.5 report. The reference column matches that report
  exactly (source_need 92.9% strict, tool_use 100% strict), which confirms the two model
  runs are scored against an identical baseline.

Raw artifacts (per-case `run.json`, acting prompts, and a machine-readable summary) live
under `evals/runs/model_routing_opus/`.

**Runtime caveat.** Opus ran inside Claude Code as one subagent per case, not as a
measured `codex exec` subprocess, so its latency and token numbers are Claude Code
subagent-reported proxies harvested from the run, not API billing — parallel to Codex's
`tokens used` proxy, but from a different tool. Because the two providers were measured by
different tools, treat these as rough ballpark figures, not an exact dollar-for-dollar
comparison. Per-case numbers are in `evals/runs/model_routing_opus/opus_runtime_proxy.json`.

**Sample-size caveat.** These are 14 and 24 single-shot cases with no repeated sampling.
Differences of one or two cases are inside the noise floor. The numbers below should be
read as "both frontier tiers clear the bar, here is where each one slips," not as a
precise model ranking.

**Scoring note.** `intent` is no longer a scored field. It steers no retrieval — `layers`,
`focus_terms`, and `query_variants` do — so it is recorded as a trace annotation and does
not gate strict case pass. These strict-pass numbers reflect that scoring. The runs on disk
were produced before the acting prompt was tightened to pull its rules from a single
rulebook, so the prompt wording here predates that fix; the scores are unaffected because
the earlier prompt already inlined the same decision rules.

## Quality

### Head-to-head (Opus 4.8 vs gpt-5.5)

Both models acted through the identical CLI-backed harness on the same 38 cases; the
recorded acting-agent reference is the same baseline both are scored against. Higher is
better except the violation/search-error rows, where lower is better.

| Suite / Metric | Opus 4.8 | gpt-5.5 (Codex) | reference |
|---|---:|---:|---:|
| **source_need** — strict case pass | 85.7% | 85.7% | 92.9% |
| source_need — search decision | 92.9% | 92.9% | 100.0% |
| source_need — layer exact | 90.0% | 90.0% | 90.0% |
| source_need — focus concept recall | 0.645 | 0.690 | 0.750 |
| **tool_use** — strict case pass | 91.7% | 95.8% | 100.0% |
| tool_use — required recall | 0.972 | 0.979 | 1.000 |
| tool_use — forbidden violations (lower better) | 4.2% | 0.0% | 0.0% |
| tool_use — false search (lower better) | 4.2% | 0.0% | 0.0% |
| tool_use — missed search (lower better) | 0.0% | 0.0% | 0.0% |

Takeaway: the two models tie on source_need (85.7%), and gpt-5.5 leads tool_use by one case
(95.8% vs 91.7%). That one case is inside the noise floor for 24 single-shot cases. The
per-suite tables below carry the same numbers with the reference row inline.

### source_need (14 cases)

| Condition | Strict Case Pass | Search Decision | Layer Exact | Focus Concept Recall |
|---|---:|---:|---:|---:|
| `claude-opus-4-8` (Claude Code agent) | 85.7% | 92.9% | 90.0% | 0.645 |
| `gpt-5.5` via Codex CLI | 85.7% | 92.9% | 90.0% | 0.690 |
| recorded acting agent reference | 92.9% | 100.0% | 90.0% | 0.750 |

### tool_use (24 cases)

| Condition | Strict Case Pass | Required Recall | Forbidden Violations | False Search | Missed Search |
|---|---:|---:|---:|---:|---:|
| `claude-opus-4-8` (Claude Code agent) | 91.7% | 0.972 | 4.2% | 4.2% | 0.0% |
| `gpt-5.5` via Codex CLI | 95.8% | 0.979 | 0.0% | 0.0% | 0.0% |
| recorded acting agent reference | 100.0% | 1.000 | 0.0% | 0.0% | 0.0% |

## Runtime

Claude Code subagent-reported proxies (not API billing), harvested from the run. Codex
figures for gpt-5.5 are shown alongside as its own-tool proxy; because the two providers
were measured by different tools, these are rough ballpark numbers, not exact.

| Suite | Model | Total tokens | Avg tokens/case | p50 latency | p95 latency |
|---|---|---:|---:|---:|---:|
| source_need (14) | `claude-opus-4-8` | 555k | 39.6k | 27.3s | 35.2s |
| source_need (14) | `gpt-5.5` (Codex) | 400k | 28.6k | 29.4s | 42.7s |
| tool_use (24) | `claude-opus-4-8` | 1.04M | 43.4k | 43.0s | 153.8s |
| tool_use (24) | `gpt-5.5` (Codex) | 1.25M | 52.0k | 71.5s | 124.0s |

Shape: Opus spends more tokens on source_need but fewer on tool_use, with faster median
latency and a heavier tail (a few long tool_use cases). Deterministic CLI work (persistence,
calculation, retrieval execution, trace validation) is identical across both and adds no
model cost.

## Failure Modes

- `claude-opus-4-8` / `source_need`: `layer_mismatch` x1 (sourceneed_v1_008),
  `false_search` x1 (sourceneed_v1_011)
- `gpt-5.5` / `source_need`: `layer_mismatch` x1 (sourceneed_v1_008), `false_search` x1
  (sourceneed_v1_011)
- `claude-opus-4-8` / `tool_use`: `missing_required:diagnose` x1 (008),
  `forbidden_action:search_source_material` x1 (008), `false_search` x1 (008),
  `missing_required:calculate` x1 (010)
- `gpt-5.5` / `tool_use`: `missing_required:diagnose` x1 (021)

## Interpretation

**The two frontier tiers behave alike.** They tie on source_need strict case pass (85.7%),
and gpt-5.5 leads tool_use by a single case (95.8% vs 91.7%). That is one case out of 24
single-shot cases with no repeated sampling, so it does not support a hard ranking.

**Source_need is now a tie.** Both models make the same two misses — one `layer_mismatch`
(008) and one `false_search` (011) — and nothing else. Opus's earlier gap was entirely in
`intent`, which is no longer scored: it steers no retrieval, so a different-but-reasonable
intent label was never a real quality difference. Once intent drops out, the two models are
even on the fields that actually drive the system.

**The remaining tool_use failures are real, and small:**

- Opus over-searched on the free-trial case (tool_use 008), producing a genuine
  `false_search` / forbidden-search / missed-diagnose triple. The free-trial / front-end
  offer area is already documented as a noisy retrieval spot in `GOLDEN_DATASET.md`, so
  this lands on a known weak point rather than a new one.
- Opus missed a required `calculate` on 010, and gpt-5.5 missed a required `diagnose` on
  021 — the one case Opus got right. So the models are not strictly ordered; each wins a
  case the other loses.

**Routing decision (unchanged).** Both `gpt-5.5` and `claude-opus-4-8` are good enough to
hold the semantic-planning role in this CLI-backed advisor: they decide when to search,
when to compute, and when to answer from state with high recall and near-zero missed
search. Deterministic work (persistence, formulas, retrieval execution, trace validation)
stays in the CLI regardless of model. This run does not justify promoting one provider over
the other for planning; it justifies keeping a strong tier for planning. A cheaper-tier
comparison is still the open work, and it must run through this same CLI-backed harness to
be comparable.
