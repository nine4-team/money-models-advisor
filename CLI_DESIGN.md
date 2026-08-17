# CLI Design

The Money Model Advisor CLI is the deterministic tool surface for an agent-operated advisor. It is not the advisor brain. A human talks to an agent; the agent uses the CLI to load state, persist facts, calculate numbers, search source material, and record traces; then the agent answers in plain English.

The CLI should make that agent workflow feel crisp, auditable, and easy to demo without turning the CLI into a brittle keyword router or a hidden answer generator.

## Product Contract

Primary user:

- an AI agent operating inside a local business context directory

Secondary users:

- a developer debugging the advisor workflow
- a reviewer inspecting state, traces, retrieval results, and eval artifacts
- a human manually running commands during development

The normal user experience should be conversational. The human should not need to know `--business-dir`, JSON payload formats, source-event schemas, or trace paths. The project skill hides that plumbing from the human and teaches the agent how to run the CLI.

## Boundary

The agent owns semantic judgment:

- decide the next advisory move
- inspect local business docs when context is missing
- decide whether source material is needed
- write one corpus-guided `SearchRequest.query`
- judge retrieved chunk usefulness
- synthesize the final answer
- decide which facts are safe to save

The CLI owns deterministic support:

- create and locate advisor state
- persist `BusinessSnapshot` facts
- run deterministic calculations
- execute retrieval against local or Pinecone-backed vector storage
- expose source chunks with IDs and scores
- record completed turns and source events
- summarize saved traces
- produce eval reports

This split is intentional. It keeps the portfolio project aligned with the real use case: a foundation-model agent uses tools. The CLI should make the agent more reliable, not replace the agent.

## Command Shape

The active CLI surface is organized around a turn lifecycle.

### 1. Start A Turn

`session start --business-dir <path> --user-message <text>`

Purpose: prepare the agent to advise.

Responsibilities:

- initialize `.money-model-advisor/` if needed
- load the saved `BusinessSnapshot`
- show advisory status, known facts, and missing fields
- show recent turn summaries
- remind the agent which operations are available
- remind the agent what must be recorded at the end of the turn

Non-responsibilities:

- do not answer the user
- do not decide the next action
- do not inspect local docs
- do not search source material automatically

This is the preferred first command for an agent-operated advisor turn.

### 2. Update Saved Context

`snapshot --business-dir <path>`

`snapshot set --business-dir <path> field=value ...`

Purpose: read and update accepted business facts.

Use this when the human states a fact, or when the agent inspects local docs and finds a clear fact worth caching. Facts saved here become part of the business snapshot, which reduces repeated local-doc inspection and token use in later turns.

The CLI may validate field paths and recompute derived readiness state. It should not infer facts or decide which facts matter.

### 3. Calculate

`calculate <metric> --inputs <json>`

Purpose: run deterministic unit-economics formulas.

Use this for CAC, gross profit, gross margin, lifetime gross profit, payback period, and CFA level. The agent should not do these calculations from memory when the CLI can run them reproducibly.

### 4. Diagnose

`diagnose --business-dir <path>`

Debug form: `diagnose --snapshot <json-or-path>`

Purpose: provide deterministic unit-economics diagnostic support from already-known numbers.

This command is a helper, not a full advisor. The agent decides whether the diagnostic result is relevant to the human's turn and how to explain it.

Agents should prefer `--business-dir` so the command reads the saved `BusinessSnapshot` directly. The raw `--snapshot` form exists for tests and manual debugging.

### 5. Search Source Material

`search --business-dir <path> --search-request-json <json> [--backend ...] [--vector-store ...]`

Purpose: retrieve citation-ready Money Models chunks from one explicit,
corpus-guided query.

The active request contains:

- `intent`: a trace label such as `teaching_evidence` or `recommendation_evidence`
- `user_turn`: the question being supported
- `query`: one concise query written from the question, saved business facts, and
  versioned corpus guide

The active query is unfiltered and runs through hybrid retrieval. If one answer needs
two genuinely different support jobs, the agent may run two searches and record two
source events. The CLI does not infer the query from shallow keywords.

Manual/debug search remains available:

`search <raw query> [--subject ...]`

This is for development and debugging, not the preferred product path.

### 6. Record A Completed Turn

`turn record --business-dir <path> ...`

Purpose: persist the completed agent-operated turn.

The record should include:

- user message
- final assistant answer
- CLI-backed actions taken
- one `source_events` entry per source-material search
- cited chunk IDs
- optional metadata
- snapshot state at the end of the turn

This is the audit trail that makes the system evaluable. It is how later commands and evals can answer, "What did the agent do, what source material did it inspect, what did it cite, and what state did it save?"

### 7. Inspect Logs

`logs --business-dir <path> [--full]`

Purpose: inspect prior advisor turns.

Use this when a new turn depends on prior conversation context, or when debugging source-event behavior.

### 8. Manage Hosted Retrieval Indexes

`index pinecone`

Purpose: upsert corpus vectors to Pinecone for hosted-vector parity and future web surfaces.

This is infrastructure/dev tooling, not part of an ordinary human advisory conversation.

## Ideal Turn Flow

```text
human asks agent
-> agent runs session start
-> agent inspects local docs if needed
-> agent saves clear facts with snapshot set
-> agent calculates if numbers are involved
-> agent searches source material only when source support is needed
-> agent answers in first person
-> agent records the completed turn
```

The turn should be useful even if no source search happens. Not every answer needs retrieval.

## Trace Model

Every recorded turn should make behavior inspectable:

- `actions`: high-level operations the agent performed
- `source_events`: structured records of source-material searches
- `cited_chunk_ids`: chunks cited in the final answer
- `metadata`: optional run/test context
- `snapshot`: business state after the turn

Source events should include:

- the `SearchRequest`
- the executed query
- retrieved or inspected chunks with IDs and scores

The trace model supports:

- user trust
- debugging
- source-event evals
- next-action/tool-use evals
- future web trace display
- hiring narrative evidence

## Output Design

CLI output should be structured JSON by default because the primary consumer is an agent or eval harness.

The JSON should be:

- compact enough for an agent to read
- stable enough for tests and evals
- explicit about paths and state files
- explicit about source IDs and retrieval settings
- free of hidden semantic decisions

Human-pretty output can be added later as `--format text` if useful, but JSON is the v1 contract.

## Naming

Use names that describe the operation in agent terms:

- `session start`: prepare the turn
- `snapshot`: read or update saved context
- `calculate`: deterministic math
- `search`: get source material
- `turn record`: save the completed turn
- `logs`: inspect prior turns

Avoid names like `chat` for the active product path because they imply the CLI is synthesizing answers. Answer synthesis belongs to the agent.

## Non-Goals

The CLI should not:

- answer as the advisor
- use external model services for agent work
- crawl business files automatically as a substitute for agent judgment
- route user intent with shallow keyword rules
- decide whether a source chunk is semantically sufficient
- hide retrieval failures behind generic answers
- require Pinecone for local development
- make a web UI depend on different advisor logic

## End-Of-Turn Trace Recording

`turn record` works as a low-level primitive, but rich `actions-json` and `source-events-json` payloads are awkward for an acting agent to assemble manually. `session finish` is the agent-facing command that makes trace recording smoother without taking semantic judgment away from the agent.

## End-Of-Turn Trace Recording Design

Implemented slice: `session finish`.

`session finish --business-dir <path> --record-json <json-or-path>`

Purpose: let the agent save one completed turn with a single structured artifact instead of manually passing several shell-escaped JSON arguments.

The agent would still decide what happened. The CLI would only validate and persist the record.

Input artifact:

```json
{
  "user_message": "what should we do next?",
  "assistant_message": "I would fix payback first...",
  "actions": [
    "session_start",
    "read_snapshot",
    "calculate",
    "search_source_material",
    "answer"
  ],
  "source_events": [
    {
      "search_request": {
        "intent": "diagnostic_evidence",
        "user_turn": "what should we do next?",
        "query": "client financed acquisition CAC gross profit payback period"
      },
      "queries": [
        "client financed acquisition CAC gross profit payback period"
      ],
      "chunks": [
        {
          "id": "payback-period:0",
          "score": 20.4
        }
      ]
    }
  ],
  "cited_chunk_ids": ["payback-period:0"],
  "metadata": {
    "run_type": "manual_agent_turn"
  }
}
```

Validation:

- require `user_message` and `assistant_message`
- require `actions` as a non-empty list of known operation labels
- allow zero `source_events`, because not every turn should search
- when `source_events` are present, require `search_request.intent`,
  `search_request.user_turn`, one non-empty `search_request.query`, the same single
  executed query, and inspected chunk IDs
- require every `cited_chunk_id` to appear in at least one source event unless `metadata.external_cited_chunk_ids` explicitly marks it as an external/non-corpus citation
- warn, but do not fail, when a source event has chunks but no cited chunks; the agent may have inspected material and decided not to cite it
- include the ending snapshot automatically, as `turn record` already does

The validator still accepts the old multi-query shape for historical trace replay.
New product traces should use only the single-query contract above.

Output:

```json
{
  "recorded": true,
  "session_path": ".../.money-model-advisor/sessions/20260611T120000.json",
  "warnings": [],
  "source_event_count": 1,
  "cited_chunk_ids": ["payback-period:0"]
}
```

Relationship to `turn record`:

- `session finish` is the preferred agent-facing command.
- `turn record` remains the lower-level primitive for tests, scripts, and manual debugging.
- Internally, `session finish` can normalize and validate the artifact, then call the same persistence helper used by `turn record`.

The goal is not more automation for its own sake. The goal is a cleaner agent-operated workflow with better traces.

## Current Gaps

The command and trace contracts are implemented. Twenty current-path answers across
five business contexts now cover source-grounded, calculation, and clarification
behavior, and `python3 scripts/regression_gate.py` packages the stable offline checks.
Add new CLI behavior only when an observed failure shows that the current operation
shape makes correct agent behavior difficult.

## Acting-Agent Test-Fix Loop

CLI quality should improve through a deliberate test-fix loop, not by adding commands speculatively.

Loop:

1. Pick 3-5 realistic user turns that exercise different advisor behaviors.
2. Send each turn to a blind acting agent with the current skill and CLI surface.
3. Require the agent to use `session start` and `session finish`.
4. Inspect saved traces, not just final answers.
5. Classify each issue by failure type.
6. Apply the smallest general fix to the right layer.
7. Rerun similar turns after the fix.
8. Promote repeated or high-risk failures into a regression case.

Failure types:

- `path_plumbing`: wrong `business_dir`, wrong repo, missing state, shell quoting problems.
- `tool_choice`: searched when it should not, failed to search when needed, skipped logs, skipped calculation, or asked unnecessary questions.
- `search_request`: search was appropriate but the single query omitted or distorted a
  concept required by the question.
- `retrieval`: the query was good but retrieved chunks were weak, noisy, or missing
  obvious support.
- `trace_shape`: actions, source events, citations, metadata, or snapshot state were missing or invalid.
- `answer_quality`: trace was valid but final advice was unclear, unsupported, too generic, or operationally weak.

Fix layer:

- Skill fix: use when the command exists but the agent used it poorly.
- CLI affordance fix: use when the command shape makes the right behavior awkward or easy to get wrong.
- Trace schema fix: use when the agent did the work but the trace cannot prove it.
- Eval/golden-case fix: use when the failure should be caught automatically next time.
- Narrative/doc fix: use when the behavior is acceptable but the design rationale is unclear.

Promotion rule:

If one agent fails because of confusing instructions, patch the skill and rerun. If two agents fail in the same way, add a regression case or trace validation. If a failure could corrupt saved state or hide unsupported advice, add a CLI guard even after one occurrence.

Completed example: calculation traces.

Recent acting-agent runs showed that agents may list `calculate` in `actions` while the saved turn does not preserve the calculation inputs or output in a structured way. That was a trace-shape gap: the agent may have calculated correctly, but the trace could not prove it. The implemented fix adds `calculation_events` to the `session finish` record schema.

`calculation_events` shape:

```json
[
  {
    "metric": "payback",
    "inputs": {
      "cac": 1000,
      "month_one_gp": 10000,
      "monthly_recurring_gp": 0
    },
    "value": 1.0
  }
]
```

Validation:

- If `actions` includes `calculate`, require at least one `calculation_events` entry.
- Each calculation event must include `metric`, `inputs`, and `value`.
- The CLI validates shape, recomputes the metric from the recorded inputs, and rejects
  an invalid input set or mismatched result.

This keeps the agent responsible for deciding when a calculation matters, while making deterministic math auditable in the saved trace.

Calculation-trace regression result:

- Five blind acting-agent cases now cover payback, gross profit, gross margin, CFA level, CAC, snapshot update after calculation, and a no-calculation vocabulary control.
- Run artifacts live under `evals/runs/calculation_trace/subagent_v1/`.
- `scripts/eval_calculation_trace_events.py --runs-dir evals/runs/calculation_trace/subagent_v1` scores 5 / 5 passing.
- One subagent initially nested `calculation_events` under `metadata`; `session finish` rejected it, and the corrected trace passed. That confirms the CLI guard is catching the right failure class.

### Current Source-Event Regression

Six isolated acting-agent runs cover multi-search, single-search, and no-search turns.
The prompts hide expected labels. The scorer requires one current `SearchRequest` per
evidence job, exact agreement between the authored and executed query, the original
user turn, and inspected chunk IDs. All six cases pass. Two answer-key corrections
were made only after the runs were frozen and are disclosed in
`evals/reports/advisor_source_event_traces.md`.
