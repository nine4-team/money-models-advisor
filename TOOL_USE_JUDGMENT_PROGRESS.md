# Tool-Use Judgment Progress

This tracker is for one problem only: whether the agent chooses the right action for a user turn.

It is separate from search-query quality. A bad search query is not the same failure as searching when the agent should have read saved state, inspected local docs, calculated, clarified, updated the snapshot, or answered directly.

## Current Status

The current CLI and skill provide the needed tool surface:

- `setup_state`
- `read_snapshot`
- `update_snapshot`
- `chat`
- `calculate`
- `search_source_material`
- `logs`

The current weakness is behavioral: the agent/CLI path can still over-trigger source-material search once the snapshot is diagnosable. That makes later turns look like retrieval problems when the real problem is tool choice.

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

- tool-use judgment accuracy

Secondary diagnostics:

- false searches: agent searched when it should not have
- missed searches: agent failed to search when source support was needed
- wrong non-search tool: agent used snapshot/logs/calculation/doc inspection incorrectly
- trace completeness: logs show the action clearly enough to audit

## Improvement Loop

1. Create the first eval set without requiring user labeling.
2. Use existing 1584 Design logs, current snapshot state, and realistic synthetic follow-up turns from the same scenario.
3. Label expected actions from the documented tool-use policy.
4. Run the current skill/CLI behavior against the cases.
5. Inspect session logs and command history.
6. Label the actual action for each turn.
7. Compare expected versus actual.
8. If wrong, revise the skill instructions or CLI affordance that caused the mistake.
9. Re-run the same case before adding new cases.

The target is not a deterministic keyword router. The target is a skill-guided agent that makes the right tool choice and leaves an auditable trace.

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
- includes clarify, calculate, source search, snapshot/log lookup, local-doc inspection, update snapshot, and direct answer cases
- no repeated generic source search on turns where source search is not the right action
- session logs make the chosen action inspectable

## Next Work

Create `evals/advisor_tool_use_cases.jsonl` from the 1584 Design conversation and add a lightweight report in `evals/reports/advisor_tool_use_judgment.md`.
