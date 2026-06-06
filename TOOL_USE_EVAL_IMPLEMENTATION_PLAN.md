# Next-Action Classification Eval Implementation Plan

This plan upgrades the next-action classification eval from a useful debugging loop into a small but methodologically sound hiring-artifact eval.

The goal is not to build a production-scale benchmark. The goal is to demonstrate senior AI engineering judgment: separate next-action classification from source-search query generation, avoid circular overclaiming, support multi-action turns, measure failure modes, and show a clear before/after improvement path.

## Eval Subject

This plan evaluates one thing: next-action classification.

Question:

```text
Given the conversation context and saved snapshot state, did the agent choose the correct next action label or action sequence for the current turn?
```

This plan does not evaluate source-search query quality. Query generation is evaluated separately in `SEARCH_QUERY_QUALITY_PROGRESS.md`, and only for cases where the correct next action is `search_source_material`.

The labels test conformance to the documented Money Model Advisor policy. They are not a claim about the one universally correct way every assistant should behave.

## Scope

V1 artifact scale:

- roughly 20-30 cases
- based on 1584 Design traces plus realistic synthetic follow-ups
- project-authored labels, validated by trace inspection
- enough to demonstrate the method and catch real failures

Production scale note:

- a production eval would expand to more businesses, more reviewers, more adversarial cases, and a larger frozen holdout
- the portfolio write-up should state this explicitly instead of pretending the small eval is a production benchmark

## P0 Design Decisions And Reasons

These decisions are the foundation for the v1 next-action classification eval.

### Saved Facts Live In Snapshot Fixtures

Decision: eval cases should not put full saved business facts into the prompt. Saved business facts should live in a snapshot fixture loaded into the eval business directory.

Reason: the eval should match the product's information architecture. If the prompt already contains the saved fact, the agent does not need to classify `read_snapshot` as the next action. To test whether the agent uses saved memory correctly, saved facts must live in the saved state.

Explanation: saved facts are business facts the advisor is supposed to remember, such as CAC, first-30-day gross profit, ICP, core offer, pricing, or something the user said earlier. A snapshot fixture is a test-only `BusinessSnapshot` file used to set up a repeatable case. Prompt text is the written context handed to the agent when the test starts. If that text already says "CAC is $1,000," the agent does not need to read saved state. "Live in" simply means "be stored in." So this decision means remembered business facts should be stored in the test snapshot file, not pasted into the text shown to the agent.

### Fresh Eval Directory Per Case

Decision: each case/run gets a fresh isolated eval business directory, such as:

```text
evals/runs/next_action/{phase}/{case_id}/business_dir
```

Reason: mutable state can contaminate the eval. If one case writes CAC into the snapshot and another case accidentally reads it, the second case is measuring test order rather than next-action classification.

Explanation: each test case should get its own temporary folder with its own `.money-model-advisor` state. The advisor writes to disk during a run. If two cases share a folder, the second case might pass only because the first case left data behind. A fresh eval directory prevents that.

### No Mutation Of Real Business State

Decision: eval runs must never mutate `/Users/benjaminmackenzie/1584_design/.money-model-advisor`.

Reason: the real 1584 directory is working business context, not an eval fixture. Reproducible evals should use copied fixtures and generated run directories.

Explanation: `/Users/benjaminmackenzie/1584_design` is real working context. Eval runs should not write to its advisor memory because that could pollute future real conversations. Tests should copy only the needed facts into disposable fixtures and run somewhere generated for the eval.

### Structured Run Artifact

Decision: every case run should write a structured `run.json` with the case ID, run phase, fixture paths, commands or workflow steps, session paths, starting snapshot hash, ending snapshot hash, and actual action trace.

Reason: if a reviewer cannot reconstruct what happened, we do not have an eval. We have a story. The run artifact turns before/after claims into inspectable evidence.

Explanation: a run artifact is a saved file, usually `run.json`, that records what happened during one test case. It should capture which case ran, which fixture was loaded, which commands ran, where logs were saved, what the starting and ending snapshots looked like, and what actions were detected. This lets us point to evidence instead of saying "I think the agent did X."

### Structured Action Trace With Confidence

Decision: actual actions should be recorded as structured objects:

```json
{
  "action": "read_snapshot",
  "confidence": "direct",
  "evidence_type": "cli_command",
  "evidence_ref": "run.json.commands[0]"
}
```

Reason: current logs do not directly expose every next-action label. Direct evidence, inferred evidence, and missing evidence need to be separated so the report does not hide weak observability.

Explanation: the action trace is the part of the run artifact that lists what actions happened. Confidence explains how strong the evidence is. `direct` means we saw a command or log event. `inferred` means the action is guessed from the answer or a side effect. `missing` means the run does not give enough evidence to classify the action.

### Headline Metrics Prefer Direct Evidence

Decision: direct evidence should anchor headline metrics. Inferred actions can be reported as debugging evidence or trace observability debt, but should not silently drive strict pass/fail.

Reason: inferred actions can turn the evaluator's interpretation into the measured behavior. Direct evidence is more auditable.

Explanation: headline metrics are the main numbers we would put in the write-up. Those numbers should be based on what the trace directly shows whenever possible. If an answer only sounds like it searched, that is useful debugging information, but it should not quietly count as a real search in the main score.

### Refined Action Taxonomy

Decision: avoid fuzzy `answer_directly` in scoring. Use clearer answer labels:

- `compose_answer_from_state`: answer synthesized from already-available conversation, snapshot, calculation, or diagnosis state
- `answer_without_tool`: answer that requires no state read, calculation, mutation, diagnosis, or retrieval

Also add:

- `diagnose`: deterministic interpretation of snapshot/calculated fields

Keep `decline_or_scope` deferred unless off-topic cases are added.

Reason: vague labels create fake disagreement. These labels separate behaviors that imply different system design choices.

Explanation: an action taxonomy is the list of labels we use for what the agent did next. `answer_directly` was too broad because it could mean answering from saved state, answering after calculation, or answering without any tool. The refined labels separate those behaviors so scoring is cleaner.

### Scenario Holdout, Not General Holdout

Decision: call the v1 untouched split `scenario_holdout`.

Reason: the v1 holdout is still based on the 1584 Design scenario. It is useful as an untouched sanity check, but it does not prove cross-business generalization.

Explanation: a holdout is a set of test cases we do not use while improving the system. We run it later as a sanity check. Because this v1 holdout is still based on the same 1584 Design scenario, `scenario_holdout` is the more honest name. It says the cases were untouched, but it does not pretend to prove the advisor works across every business.

## Action Taxonomy

Use these action labels:

| Action | Meaning |
|---|---|
| `clarify` | Ask for the next missing or ambiguous business fact |
| `update_snapshot` | Save accepted business context |
| `read_snapshot` | Read saved business facts |
| `read_logs` | Inspect prior advisor turns |
| `inspect_local_docs` | Agent reads local business docs before saving facts |
| `calculate` | Run explicit deterministic math or create a newly computed numeric field |
| `diagnose` | Interpret calculated/snapshot fields into a business constraint or advisory status |
| `search_source_material` | Search the Money Models corpus for citeable source chunks |
| `compose_answer_from_state` | Answer from already-available conversation, snapshot, calculation, or diagnosis state |
| `answer_without_tool` | Answer when no state read, calculation, mutation, diagnosis, or retrieval is needed |

## Case Schema

Create `evals/advisor_tool_use_cases.jsonl`.

Each row should use this shape:

```json
{
  "case_id": "tooluse_v1_001",
  "split": "dev",
  "scenario_id": "1584_design",
  "turn_type": "saved_fact_lookup",
  "conversation_context": "The user previously said referral partners cost about $1k per client.",
  "snapshot_state": "Snapshot has CAC=$1k and first-30-day gross profit=$10k.",
  "user_turn": "what happened to the $1k we pay to referral partners?",
  "required_actions": ["read_snapshot"],
  "allowed_actions": ["read_logs", "compose_answer_from_state"],
  "forbidden_actions": ["search_source_material"],
  "expected_first_action": "read_snapshot",
  "search_allowed": false,
  "label_rationale": "The user is asking about saved business context, not Money Models source material.",
  "ambiguity": "low",
  "severity_if_wrong": "high"
}
```

Design choice:

- score required, allowed, and forbidden actions instead of a single `expected_action`
- this handles valid multi-step turns such as `read_snapshot -> calculate -> compose_answer_from_state`
- keep `expected_first_action` because the first action choice is often where bad behavior starts

## Case Balance

The first v1 case set should include at least two cases for each major action class:

| Action class | Minimum v1 cases |
|---|---:|
| `clarify` | 2 |
| `update_snapshot` | 2 |
| `read_snapshot` or `read_logs` | 2 |
| `inspect_local_docs` | 2 |
| `calculate` | 2 |
| `search_source_material` | 2 |
| `compose_answer_from_state` | 2 |
| `answer_without_tool` | 2 |

Include control cases:

- at least two negative controls where `search_source_material` is clearly wrong
- at least two positive controls where `search_source_material` is clearly required

## Split Strategy

Use a tiny split structure to demonstrate eval discipline without overbuilding:

| Split | Purpose | Suggested v1 size |
|---|---|---:|
| `dev` | Cases used to inspect failures and improve skill/tool guidance | 12-18 |
| `regression` | Cases for previously observed bugs, especially generic repeated search | 4-6 |
| `scenario_holdout` | Untouched same-scenario cases; run after changes as a sanity check | 4-6 |

Important:

- It is okay for v1 `scenario_holdout` to be small.
- The write-up should not overclaim from the `scenario_holdout`.
- The point is to show the method: tune on dev/regression, then sanity-check on untouched cases.

## Scoring

Create `scripts/eval_tool_use_judgment.py`.

Inputs:

- `evals/advisor_tool_use_cases.jsonl`
- actual trace/action records from the current run

Output:

- `evals/reports/advisor_tool_use_judgment.md`
- optionally `evals/runs/tool_use_judgment_*.json`

Metrics:

- first-action accuracy
- required-action recall
- forbidden-action violation rate
- false-search rate
- missed-search rate
- full-sequence pass rate
- per-turn-type breakdown
- trace completeness

Definitions:

- false search: `search_source_material` appears when it is forbidden
- missed search: `search_source_material` is required but absent
- required-action recall: required actions present in the actual action sequence
- full-sequence pass: all required actions present and no forbidden actions present
- trace completeness: actual actions can be recovered from logs without guessing

V1 thresholds:

- regression false-search rate on cases where search is forbidden: 0
- forbidden source search on saved-context lookup cases: 0
- trace completeness: at least 95%
- required-action recall on dev/regression: at least 80%
- `scenario_holdout` results are reported descriptively and are not used for a strong generalization claim

## Actual Action Extraction

Define actual actions from the session trace and command history, not from subjective answer quality. The eval report must include the case ID, expected actions, actual actions, trace path or run ID, and failure rationale for every failed case.

Mapping:

- `retrieval_queries` or `evidence` present -> `search_source_material`
- calculator action or deterministic payback/gross-margin computation -> `calculate`
- snapshot read command -> `read_snapshot`
- logs command -> `read_logs`
- snapshot field update -> `update_snapshot`
- local file reads in business directory -> `inspect_local_docs`
- assistant asks for missing field and no other stronger tool action occurs -> `clarify`
- assistant answers from already-available conversation, snapshot, calculation, or diagnosis state -> `compose_answer_from_state`
- assistant answers without any state read, calculation, mutation, diagnosis, or retrieval -> `answer_without_tool`

If a trace cannot be classified, mark trace completeness as failed and record the case for logging improvement.

## Ambiguity Handling

Use the `ambiguity` field to avoid fake precision:

| Ambiguity | Scoring rule |
|---|---|
| `low` | Include in headline metrics. Score normally. |
| `medium` | Include in headline metrics, but use `allowed_actions` to avoid penalizing reasonable alternate paths. Do not penalize first action unless it is materially harmful or forbidden. |
| `high` | Exclude from headline metrics. Report qualitatively as an analysis case. |

High-ambiguity cases can be useful for design discussion, but they should not drive the headline score.

## Baseline And Improvement Loop

1. Build the eval cases and scorer.
2. Run current behavior as the baseline.
3. Produce a report with failures by split and turn type.
4. Improve skill instructions or CLI affordances based on dev/regression failures.
5. Re-run dev and regression cases.
6. Run `scenario_holdout` only after the improvement pass.
7. Document before/after metrics.

Do not tune directly on `scenario_holdout` failures. If a `scenario_holdout` failure reveals a new class of issue, move it into a future dev/regression set and create fresh `scenario_holdout` cases before making stronger claims.

## Success Criteria For V1

V1 is successful if it shows:

- repeated generic source search is reduced or eliminated on non-search turns
- regression false-search rate on search-forbidden cases reaches 0
- no forbidden source search on saved-context lookup cases
- required-action recall is at least 80% on dev/regression cases
- trace completeness is at least 95%
- `scenario_holdout` results are reported descriptively and do not immediately contradict the dev/regression improvement

V1 is not required to prove production robustness.

## Hiring Artifact Framing

In the final narrative, describe this as:

> a small-scale next-action classification eval, with source-search query generation evaluated separately and a clear path to production scaling.

Do not describe it as:

> a comprehensive production benchmark.

The strength of the artifact is the thinking: precise problem decomposition, non-circular scoring, traceability, and before/after improvement.

## Next Steps

Before creating cases or writing the scorer, work through the senior-review backlog below.

## Senior Review Backlog

Status legend:

- `open`: not yet addressed
- `planned`: accepted and reflected in this plan
- `done`: implemented in code or eval artifacts

### P0 — Must Fix Before Implementation

These items determine whether the eval is auditable and trustworthy.

| Priority | Item | Status | Why it matters |
|---|---|---|---|
| P0 | Define run protocol | planned | Each case needs a reproducible mapping from `case_id` to business dir, run ID, session path, trace file, and baseline/post-change status. |
| P0 | Add structured action trace target | planned | Current logs do not directly expose all next-action labels, so the eval needs a structured action record instead of brittle inference. |
| P0 | Tighten action taxonomy | planned | `answer_directly` and `calculate` were too fuzzy to score reproducibly; the plan now uses `compose_answer_from_state`, `answer_without_tool`, `calculate`, and `diagnose`. |
| P0 | Separate direct vs inferred trace evidence | planned | The report should show whether an action was directly logged, inferred, or missing. |
| P0 | Prevent per-case state contamination | planned | Cases need fresh or explicitly prepared state so prior runs do not affect later labels. |

### P1 — Should Fix For A Strong First Report

These items improve scoring quality and make the report easier to trust.

| Priority | Item | Status | Why it matters |
|---|---|---|---|
| P1 | Add labeling guide | open | Labels should be reproducible and should include examples for low, medium, and high ambiguity. |
| P1 | Add failure taxonomy | open | Failure types make the report more useful than a raw accuracy number. |
| P1 | Make regression set risk-weighted | open | Regression should overweight the known bug: repeated source search after diagnosable state. |
| P1 | Add trace parse/directness metrics | open | Distinguishes "we can parse something" from "the system directly logged the intended action." |
| P1 | Add control cases | planned | Include cases where search is clearly wrong and clearly required. |
| P1 | Add label review note | open | Project-authored labels are fine for v1, but the report should identify any double-reviewed or user-reviewed labels. |

### P2 — Future Production-Scale Notes

These items are not required for the small hiring artifact, but should be acknowledged in the final narrative.

| Priority | Item | Status | Why it matters |
|---|---|---|---|
| P2 | Rename holdout framing to scenario holdout | planned | Current holdout is same-scenario, not cross-business generalization. |
| P2 | Add future cross-business holdout note | planned | Clarifies how this would scale beyond the 1584 Design proof. |
| P2 | Expand case count and reviewers for production | planned | Production eval would need more businesses, more cases, and stronger reviewer coverage. |

## Revised Immediate Order

1. Define the run protocol.
2. Define the structured action trace target.
3. Tighten the action taxonomy.
4. Add the labeling guide and failure taxonomy.
5. Create `evals/advisor_tool_use_cases.jsonl`.
6. Write `scripts/eval_tool_use_judgment.py`.
7. Generate the first baseline report.
8. Improve the skill/tool guidance from dev/regression failures.
9. Re-run and record before/after results.
