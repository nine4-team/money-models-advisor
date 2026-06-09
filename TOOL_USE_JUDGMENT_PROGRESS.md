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
- `scripts/eval_tool_use_judgment.py`
- `evals/reports/advisor_tool_use_judgment.md`

The current report is intentionally case inventory only because no `run.json` traces have been captured yet. The next missing piece is a trace-capture workflow that runs or records the skill-guided agent behavior in isolated eval directories.

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
4. Run the current skill/CLI behavior against the cases.
5. Inspect session logs and command history.
6. Label the actual action for each turn.
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

1. Build or capture isolated `run.json` traces for the existing cases.
2. Re-run `python3 scripts/eval_tool_use_judgment.py`.
3. Use the generated report as the baseline.
4. Improve skill/tool guidance from dev/regression failures.
5. Re-run dev/regression, then run `scenario_holdout` after the improvement pass.
