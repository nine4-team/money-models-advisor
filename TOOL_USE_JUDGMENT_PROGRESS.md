# Next-Action Classification Progress

This tracker is for one problem only: whether the agent correctly classifies the next action for a user turn.

It is separate from search-query quality. A bad search query is not the same failure as choosing `search_source_material` when the correct next action was to read saved state, inspect local docs, calculate, clarify, update the snapshot, compose from state, or answer without a tool.

## Current Status

The current CLI and skill provide the needed tool surface:

- `setup_state`
- `read_snapshot`
- `update_snapshot`
- `chat`
- `calculate`
- `search_source_material`
- `logs`

The current weakness is next-action classification: the agent/CLI path can still over-trigger source-material search once the snapshot is diagnosable. That makes later turns look like retrieval problems when the real problem is the next-action label.

The v1 case set and scorer now exist:

- `evals/advisor_tool_use_cases.jsonl`
- `scripts/capture_tool_use_trace.py`
- `scripts/eval_tool_use_judgment.py`
- `evals/reports/advisor_tool_use_judgment.md`

The trace recorder has been piloted on five dev cases:

- `tooluse_v1_001`: saved fact lookup
- `tooluse_v1_003`: business fact update
- `tooluse_v1_005`: local doc lookup
- `tooluse_v1_007`: calculation
- `tooluse_v1_009`: source-material search

All five completed traces validate and score cleanly in `evals/reports/advisor_tool_use_judgment.md`.

The remaining dev/regression traces have also been captured. Scenario holdout was then run after freezing generated prompts, using separate acting agents that saw only `acting_prompt.md` content and not expected labels.

Current report status:

- dev: 14/14 scored
- regression: 5/5 scored
- scenario_holdout: 5/5 scored
- first-action accuracy across all captured traces: 95.8%
- required-action recall across all captured traces: 1.000
- false-search rate across all captured traces: 0%
- missed-search rate across all captured traces: 0%
- trace completeness across all captured traces: 100%

Important caveat: dev/regression traces were captured in-thread by Codex to verify the recorder, schema, evidence refs, and policy-conformance scoring. Scenario holdout is stronger because prompts were frozen before execution and separate actors saw only acting prompts, but it is still not a production-grade independent benchmark.

Observed holdout failure:

- `tooluse_v1_023`: wrong first action. The actor read the snapshot before reading logs on a prior-conversation recall question. It still read logs before answering, so required-action recall passed; the failure is about first-action priority.

Key design choice: build a trace recorder, not a deterministic planner. The recorder should set up fixtures, capture commands and files, extract observable `actual_actions[]`, and write `run.json`. It should not choose the next action from the case label. The actor, trace extractor, and scorer should remain separate so the eval measures agent judgment rather than a hard-coded runner or self-report.

## Known Failure Modes

From the 1584 Design trace review:

| User turn type | Correct action | Current risk |
|---|---|---|
| User gives a business fact | `update_snapshot`, then maybe `chat` | Treating it as a diagnostic search turn |
| User asks what happened earlier | `read_snapshot` or `logs` | Searching the source corpus |
| User asks for a calculation | `calculate` or deterministic snapshot math | Searching before calculating |
| User asks for a concept explanation | `search_source_material` if source support is useful | No search, or generic diagnostic search |
| User asks for a recommendation | calculate plus targeted source search | Generic diagnostic search |
| User asks a broad opener | clarify or summarize known context | Premature search |

## Evaluation Strategy

Build a small turn-level eval set from realistic conversations. Each row should include:

- conversation context summary
- current user turn
- snapshot state summary
- expected tool/action
- whether source-material search is allowed
- reason for the expected action

Primary metric:

- next-action classification accuracy

Secondary diagnostics:

- false searches: agent searched when it should not have
- missed searches: agent failed to search when source support was needed
- wrong non-search tool: agent used snapshot/logs/calculation/doc inspection incorrectly
- trace completeness: logs show the action clearly enough to audit

## Improvement Loop

1. Create the first eval set without requiring user labeling.
2. Use existing 1584 Design logs, current snapshot state, and realistic synthetic follow-up turns from the same scenario.
3. Label expected actions from the documented advisor policy.
4. Run the current skill-guided agent behavior against the cases without exposing expected labels.
5. Record observable commands, file reads, session logs, snapshot hashes, and final answers.
6. Extract the actual action trace for each turn from evidence.
7. Compare expected versus actual.
8. If wrong, revise the skill instructions or CLI affordance that caused the mistake.
9. Re-run the same case before adding new cases.

The target is not a deterministic keyword router. The target is a skill-guided agent that classifies the next action correctly and leaves an auditable trace.

The human reviewer should not need to label the first pass. The handoff point is the generated report: once the eval set, scorer, and first iteration are complete, ask the human to review the failure patterns and any ambiguous expected-action labels.

## No-User-Loop First Pass

Codex should handle the first pass end to end:

1. Create `evals/advisor_tool_use_cases.jsonl` with roughly 20 cases.
2. Include cases from the 1584 Design conversation plus realistic synthetic follow-ups.
3. Label expected actions using the project docs, not external model-service calls.
4. Write a lightweight scorer/report generator.
5. Run the current behavior and document failure patterns.
6. Iterate on the skill/tool guidance until the repeated generic-search failure is materially reduced.
7. Bring the user the report for review, not raw labeling work.

The report should be transparent that initial labels were project-authored and validated by trace inspection.

## Done Criteria

For the first v1 pass:

- at least 15 realistic turns labeled
- includes clarify, calculate, diagnose, source search, snapshot/log lookup, local-doc inspection, update snapshot, compose-from-state, and answer-without-tool cases
- no repeated generic source search on turns where source search is not the right action
- session logs make the chosen action inspectable

## Next Work

Follow `TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md`.

Immediate implementation steps:

1. Decide whether `tooluse_v1_023` is a true guidance failure or an overly strict first-action label.
2. If guidance changes, update the skill/operating guide and re-run dev/regression before creating a fresh holdout.
3. If the label changes, mark the original holdout case as adjudicated rather than silently rewriting history.
4. Update the narrative with the final baseline and caveat.
