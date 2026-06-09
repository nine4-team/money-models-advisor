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

## Evaluated System Boundary

V1 evaluates the skill-guided agent planner, not the deterministic internals of `money-model-advisor chat`.

The evaluated behavior is:

```text
case context + saved fixture state + available CLI tools
→ agent chooses the next action label or action sequence
→ agent runs CLI commands when needed
→ evaluator captures the observable command/session trace
```

This boundary matches the product architecture: a human talks to an agent, and the agent uses the skill to operate the CLI. The CLI is the tool surface, state store, calculator, search endpoint, and trace writer. It is not the full planner being evaluated in this v1.

This means actions such as `read_snapshot`, `read_logs`, and `inspect_local_docs` are evaluated as agent-level actions. They should be evidenced by captured CLI commands or file-inspection steps, not by assuming that `chat` internally loaded state.

## Scope

V1 artifact scale:

- roughly 20-30 cases
- based on 1584 Design traces plus realistic synthetic follow-ups
- project-authored labels, validated by trace inspection
- enough to demonstrate the method and catch real failures

Production scale note:

- a production eval would expand to more businesses, more reviewers, more adversarial cases, and a larger frozen holdout
- the portfolio write-up should state this explicitly instead of pretending the small eval is a production benchmark

## Product Cases Vs Harness Checks

The main next-action classification eval should contain product-behavior cases: realistic turns a user might say while using the advisor. These cases test whether the skill-guided agent chooses the right next action for the product workflow.

Harness or operability checks are different. They test whether the evaluation machinery, developer terminology, and reports are understandable and internally consistent. Examples include:

- "what does false search mean?"
- "what does scenario_holdout mean?"
- "what is a trace?"
- "what does direct evidence mean?"

Those are useful checks, but they should not be mixed into the product-behavior eval or included in headline advisor-quality metrics. If we want them, put them in a separate future file such as `evals/harness_operability_cases.jsonl` and report them as harness checks, not as user-realism evidence.

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

### Trace Recorder, Not Deterministic Planner

Decision: the next-action eval should use a trace recorder, not a deterministic script that decides which advisor action to take.

Reason: the eval subject is the skill-guided agent's judgment. If the runner deterministically chooses `read_snapshot`, `search_source_material`, `calculate`, or another action from the case label, the runner replaces the behavior we are trying to measure. That would test the runner's hard-coded policy, not the agent's next-action classification.

Explanation: a trace recorder sets up the case, captures what the agent actually did, and writes evidence into `run.json`. It may record commands, file reads, session paths, stdout, stderr, final answer text, snapshot hashes, and observed action evidence. It should not decide the correct next action for the agent. The case label is for the evaluator, not for the acting agent.

### Separate Actor, Trace Extraction, And Scoring

Decision: keep three roles separate:

- the acting agent performs the case using the skill and CLI
- the trace extractor maps observable steps into `actual_actions[]`
- the scorer compares `actual_actions[]` against the case label

Reason: if the acting agent labels its own behavior without observable evidence, the metric can become self-report. Separating the roles keeps the report auditable and makes weak evidence visible.

Explanation: the acting agent can say what it did, but the eval should prefer commands, logs, file-inspection records, session fields, and snapshot diffs. When an action is not directly visible, the extractor can mark it `inferred` or `missing`. The scorer should not silently convert a plausible story into a hard pass.

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
  "snapshot_fixture_path": "evals/fixtures/snapshots/1584_payback_ready.json",
  "local_docs_fixture_path": null,
  "prior_sessions_fixture_path": "evals/fixtures/sessions/1584_referral_partner_context.json",
  "user_turn": "what happened to the $1k we pay to referral partners?",
  "required_actions": ["read_snapshot"],
  "allowed_actions": ["read_logs", "compose_answer_from_state"],
  "forbidden_actions": ["search_source_material"],
  "expected_first_action": "read_snapshot",
  "search_allowed": false,
  "expected_mutation": "none",
  "label_rationale": "The user is asking about saved business context, not Money Models source material.",
  "ambiguity": "low",
  "severity_if_wrong": "high"
}
```

Design choice:

- score required, allowed, and forbidden actions instead of a single `expected_action`
- this handles valid multi-step turns such as `read_snapshot -> calculate -> compose_answer_from_state`
- keep `expected_first_action` because the first action choice is often where bad behavior starts
- use fixture paths instead of prose `snapshot_state`, so cases are repeatable

## Fixture Schema

Each case should reference structured fixtures instead of relying on prose setup.

| Field | Required | Meaning |
|---|---|---|
| `snapshot_fixture_path` | yes | JSON fixture copied into the case's eval business directory as the starting `BusinessSnapshot`. |
| `local_docs_fixture_path` | no | Directory or file fixture copied into the eval business directory when the expected action may inspect local business docs. |
| `prior_sessions_fixture_path` | no | Session/log fixture copied into `.money-model-advisor/sessions/` when the expected action may read prior turns. |
| `expected_mutation` | yes | Expected state mutation policy: `none`, `snapshot_update`, or `session_only`. |

The fixture loader should record starting and ending snapshot hashes in `run.json`.

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

## Run Protocol

Each eval case runs in an isolated generated directory:

```text
evals/runs/next_action/{phase}/{case_id}/business_dir
```

The runner should:

1. Create a fresh run directory for the case.
2. Copy the snapshot fixture into `business_dir/.money-model-advisor/business_snapshot.json`.
3. Copy local-doc and prior-session fixtures when the case references them.
4. Record the starting snapshot hash.
5. Present the case to the skill-guided acting agent without exposing expected labels.
6. Capture CLI commands, file-inspection steps, stdout/stderr, session paths, and final answer.
7. Extract `actual_actions[]` from observable trace evidence.
8. Record the ending snapshot hash.
9. Write `run.json`.

Never run eval cases against `/Users/benjaminmackenzie/1584_design/.money-model-advisor`.

The trace recorder may automate setup and capture, but it must not use the case's expected actions to choose commands for the acting agent.

## `run.json` Schema

Every case run should produce a structured artifact:

```json
{
  "case_id": "tooluse_v1_001",
  "split": "dev",
  "phase": "baseline",
  "business_dir": "evals/runs/next_action/baseline/tooluse_v1_001/business_dir",
  "fixtures": {
    "snapshot_fixture_path": "evals/fixtures/snapshots/1584_payback_ready.json",
    "local_docs_fixture_path": null,
    "prior_sessions_fixture_path": "evals/fixtures/sessions/1584_referral_partner_context.json"
  },
  "snapshot_hash": {
    "start": "sha256:...",
    "end": "sha256:..."
  },
  "workflow_steps": [
    {
      "index": 0,
      "kind": "cli_command",
      "command": "money-model-advisor snapshot --business-dir ...",
      "stdout_path": "stdout/000_snapshot.txt",
      "stderr_path": "stderr/000_snapshot.txt",
      "exit_code": 0
    }
  ],
  "session_paths": [
    "business_dir/.money-model-advisor/sessions/....json"
  ],
  "actual_actions": [
    {
      "index": 0,
      "action": "read_snapshot",
      "confidence": "direct",
      "evidence_type": "cli_command",
      "evidence_ref": "workflow_steps[0]"
    }
  ],
  "final_answer_path": "final_answer.txt"
}
```

## Normalized Action Trace

Each `actual_actions[]` item should use this shape:

```json
{
  "index": 0,
  "action": "search_source_material",
  "confidence": "direct",
  "evidence_type": "session.retrieval_queries",
  "evidence_ref": "business_dir/.money-model-advisor/sessions/....json:retrieval_queries[0]"
}
```

Allowed confidence values:

- `direct`: explicit command, file-inspection step, session field, or structured run event
- `inferred`: implied by prose, side effect, or final answer but not explicitly logged
- `missing`: expected evidence is absent or unclassifiable

Headline metrics should require direct evidence for tool-like actions:

- `read_snapshot`
- `read_logs`
- `inspect_local_docs`
- `update_snapshot`
- `calculate`
- `diagnose`
- `search_source_material`

Answer-like actions can be reported separately as response classification when they are inferred from the final answer:

- `compose_answer_from_state`
- `answer_without_tool`

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

## Observability By Action

| Action | V1 observability | Direct evidence examples |
|---|---|---|
| `clarify` | inferred | final answer asks for a missing field and no stronger tool-like action occurs |
| `update_snapshot` | direct | `snapshot set` command, snapshot diff, or session action showing field update |
| `read_snapshot` | direct | `snapshot` CLI command in `workflow_steps` |
| `read_logs` | direct | `logs` CLI command in `workflow_steps` |
| `inspect_local_docs` | direct | recorded file-inspection step under the eval business dir |
| `calculate` | direct | `calculate` command or structured calculator event |
| `diagnose` | direct or inferred | `diagnose` command, structured diagnosis event, or diagnosis fields added to snapshot |
| `search_source_material` | direct | `search` command, `retrieval_queries`, or `evidence` |
| `compose_answer_from_state` | inferred | final answer uses existing context after allowed state/calculation actions |
| `answer_without_tool` | inferred | final answer with no state read, calculation, mutation, diagnosis, or retrieval |

## Ambiguity Handling

Use the `ambiguity` field to avoid fake precision:

| Ambiguity | Scoring rule |
|---|---|
| `low` | Include in headline metrics. Score normally. |
| `medium` | Include in headline metrics, but use `allowed_actions` to avoid penalizing reasonable alternate paths. Do not penalize first action unless it is materially harmful or forbidden. |
| `high` | Exclude from headline metrics. Report qualitatively as an analysis case. |

High-ambiguity cases can be useful for design discussion, but they should not drive the headline score.

## Labeling Guide

Labels are policy-conformance labels. They answer: under the documented Money Model Advisor design, what next action should the skill-guided agent choose?

General rules:

1. Do not label source-material search as required unless the answer needs Money Models source support.
2. Do not label saved business facts as prompt context. If the fact should be remembered, put it in the snapshot or prior-session fixture.
3. Use `required_actions` for actions that must happen.
4. Use `allowed_actions` for reasonable supporting actions.
5. Use `forbidden_actions` for harmful or misleading actions, especially false source searches.
6. Prefer low-ambiguity cases for headline metrics.
7. Mark high-ambiguity cases as analysis cases, not headline scoring cases.

Boundary examples:

| Boundary | Labeling rule |
|---|---|
| `clarify` vs `answer_without_tool` | Use `clarify` when a needed business fact is missing or ambiguous. Use `answer_without_tool` only when the agent can answer without saved state, calculation, diagnosis, mutation, or retrieval. |
| `calculate` vs `diagnose` | Use `calculate` for explicit deterministic math or creating a numeric field. Use `diagnose` when interpreting numbers into a constraint, advisory status, or business implication. |
| `read_snapshot` vs `compose_answer_from_state` | Use `read_snapshot` when the agent must inspect saved business facts. Use `compose_answer_from_state` when the relevant state is already available from prior allowed actions in the same run. |
| `search_source_material` required vs allowed | Required when source support is necessary to teach, explain, compare, or justify. Allowed when citations would be helpful but not necessary. Forbidden when the user is asking about saved business context, local docs, or calculations. |
| `inspect_local_docs` vs `read_snapshot` | Use `inspect_local_docs` when the fact is expected to exist in local business documents but has not been accepted into the snapshot. Use `read_snapshot` when the fact should already be saved. |

Ambiguity examples:

| Ambiguity | Example | Handling |
|---|---|---|
| `low` | "What did I say CAC was?" with CAC in snapshot fixture | Require `read_snapshot`; forbid `search_source_material`. |
| `medium` | "Where does this leave us?" after numbers are complete | Allow `calculate`, `diagnose`, and `compose_answer_from_state`; require only the action needed by the case rationale. |
| `high` | "What should I do?" with unclear goal and partial context | Exclude from headline metrics; use qualitatively. |

Materially harmful first actions:

- searching source material when search is forbidden
- recommending before required facts are known
- calculating from missing or stale values
- updating snapshot with an unconfirmed or contradicted fact
- inspecting local docs when the answer should come from saved state or logs

## Failure Taxonomy

Use these failure types in reports:

| Failure type | Meaning |
|---|---|
| `false_search` | `search_source_material` happened when it was forbidden. |
| `missed_search` | `search_source_material` was required but absent. |
| `wrong_state_tool` | The agent used the wrong state source, such as local docs instead of snapshot/logs. |
| `missed_state_lookup` | The case required `read_snapshot` or `read_logs`, but the agent did not inspect saved state. |
| `premature_clarify` | The agent asked a question even though the needed fact was available in fixture state. |
| `premature_recommendation` | The agent recommended before required facts, calculations, or source support were available. |
| `missed_calculation` | `calculate` was required but absent. |
| `missed_diagnosis` | `diagnose` was required but absent. |
| `stale_query_reuse` | The agent reused a generic or previous search query that did not match the current turn. |
| `forbidden_action` | Any action listed in `forbidden_actions` occurred. |
| `wrong_first_action` | The first action was incorrect or materially harmful, even if later actions recovered. |
| `unlogged_action` | The action may have happened, but the trace does not provide enough evidence. |
| `state_contamination` | The case result depends on state not present in the fixture. |

Regression cases should overweight the known failure mode: once a snapshot is diagnosable, the system can repeat generic source search on turns that need saved-state lookup, calculation, local-doc inspection, or composition from state.

## Trace Metrics

Add these diagnostics to the report:

| Metric | Meaning |
|---|---|
| `trace_parse_rate` | Percent of cases where the evaluator can extract an action trace at all. |
| `trace_directness_rate` | Percent of actual actions supported by direct evidence. |
| `inferred_action_count` | Number of actions scored as inferred rather than direct. |
| `missing_trace_count` | Number of expected or claimed actions with missing evidence. |

Trace metrics are diagnostic metrics. They explain how trustworthy the eval evidence is; they should not be confused with next-action classification quality.

## Label Review Note

The first v1 labels can be project-authored by Codex from the documented advisor policy. The report should state this plainly.

Before final publication, record:

- how many labels were project-authored
- how many labels were reviewed by the user or a second reviewer
- which labels were marked medium or high ambiguity
- which labels were excluded from headline metrics

This is enough for the hiring artifact. Production use would require broader reviewer coverage.

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
| P0 | Define run protocol | done | Each case needs a reproducible mapping from `case_id` to business dir, run ID, session path, trace file, and baseline/post-change status. |
| P0 | Add structured action trace target | done | Current logs do not directly expose all next-action labels, so the eval needs a structured action record instead of brittle inference. |
| P0 | Use trace recorder, not deterministic planner | done | The runner must capture the agent's choices, not replace them with hard-coded case-label behavior. |
| P0 | Separate actor, trace extraction, and scoring | done | Prevents self-report from becoming the metric and keeps weak evidence visible. |
| P0 | Tighten action taxonomy | done | `answer_directly` and `calculate` were too fuzzy to score reproducibly; the plan now uses `compose_answer_from_state`, `answer_without_tool`, `calculate`, and `diagnose`. |
| P0 | Separate direct vs inferred trace evidence | done | The report should show whether an action was directly logged, inferred, or missing. |
| P0 | Prevent per-case state contamination | done | Cases need fresh or explicitly prepared state so prior runs do not affect later labels. |

### P1 — Should Fix For A Strong First Report

These items improve scoring quality and make the report easier to trust.

| Priority | Item | Status | Why it matters |
|---|---|---|---|
| P1 | Add labeling guide | done | Labels should be reproducible and should include examples for low, medium, and high ambiguity. |
| P1 | Add failure taxonomy | done | Failure types make the report more useful than a raw accuracy number. |
| P1 | Make regression set risk-weighted | done | Regression should overweight the known bug: repeated source search after diagnosable state. |
| P1 | Add trace parse/directness metrics | done | Distinguishes "we can parse something" from "the system directly logged the intended action." |
| P1 | Add control cases | done | Include cases where search is clearly wrong and clearly required. |
| P1 | Add label review note | planned | Project-authored labels are fine for v1, but the report should identify any double-reviewed or user-reviewed labels. |

### P2 — Future Production-Scale Notes

These items are not required for the small hiring artifact, but should be acknowledged in the final narrative.

| Priority | Item | Status | Why it matters |
|---|---|---|---|
| P2 | Rename holdout framing to scenario holdout | planned | Current holdout is same-scenario, not cross-business generalization. |
| P2 | Add future cross-business holdout note | planned | Clarifies how this would scale beyond the 1584 Design proof. |
| P2 | Expand case count and reviewers for production | planned | Production eval would need more businesses, more cases, and stronger reviewer coverage. |
| P2 | Add separate harness/operability checks | planned | Eval/procedure-vocabulary checks are useful for developer confidence, but should not be mixed into product-behavior metrics. |

## Revised Immediate Order

1. Define the run protocol.
2. Define the structured action trace target.
3. Tighten the action taxonomy.
4. Add the labeling guide and failure taxonomy.
5. Create `evals/advisor_tool_use_cases.jsonl`.
6. Write `scripts/capture_tool_use_trace.py`.
7. Write `scripts/eval_tool_use_judgment.py`.
8. Generate the first case-inventory report.
9. Pilot trace capture on 3-5 dev cases.
10. Improve the skill/tool guidance from dev/regression failures.
11. Re-run and record before/after results.
