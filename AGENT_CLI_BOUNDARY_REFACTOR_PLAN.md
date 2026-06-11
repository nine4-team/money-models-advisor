# Agent/CLI Boundary Refactor Plan

This plan fixes the architectural boundary identified during source-need evaluation:

- the agent judges meaning
- the CLI handles deterministic bookkeeping

The goal is not to redo the project. The goal is to put already-built pieces in the right role so future evals measure the agent-operated advisor rather than a deterministic mini-advisor.

## Preserve

These pieces remain valid:

- `BusinessSnapshot` as cached accepted business state
- deterministic unit-economics formulas and numeric/accounting state classification
- local corpus search over Money Models transcripts
- trace capture and report generation
- next-action eval structure where acting agents perform cases and CLI scripts score traces
- source-need eval structure where acting agents generate `SourceNeed`
- source-query quality eval when an explicit `SourceNeed` is supplied

## Remove Or Replace

These pieces should not remain in the product path:

- exact focus-term substring recall: keep as a debugging metric, not a semantic quality score
- status-driven query generation from `build_advisor_queries(snapshot)` without a `SourceNeed`
- deterministic `chat` answer synthesis as the visible advisor brain
- retrieval metrics that assume a query should have been generated before the agent has selected source search

## Target Command Contract

Before changing eval machinery, define the product-facing command contract:

- The agent remains the semantic planner.
- `chat` must not be the semantic answer engine in product-facing usage.
- Add `turn record` as the persistence command.
- Remove `chat` from the target product workflow instead of preserving a compatibility path.
- Source-backed turns must record:
  - agent-selected `SourceNeed`
  - generated query or direct search query
  - returned chunks
  - cited chunk IDs
  - final answer or answer summary

Open implementation choice: the source-search CLI surface should become explicit. The likely v1 options are:

- add `search --source-need-json ...` and let the CLI build the corpus query from `SourceNeed`
- add `query build --source-need-json ...` as a query-construction helper, then agent calls `search`
- keep `search "raw query" --layer ...` but require the agent to record the `SourceNeed` that produced the query

The first option is the cleanest product path because it keeps the source need attached to the search artifact.

## Refactor

### 1. Repair Chat / Turn Persistence Boundary

Target behavior:

- the agent decides whether to clarify, calculate, search, update snapshot, inspect logs, or answer
- CLI commands persist turns, run deterministic functions, execute search, and record artifacts
- `chat` no longer acts as the primary semantic planner in product-facing usage

V1 shape:

- replace product-facing use of `chat` with `turn record`
- remove or archive deterministic `chat` synthesis rather than maintaining compatibility

Why:

The current `run_single_turn()` path still extracts facts, diagnoses, builds queries, retrieves evidence, and synthesizes answers in one deterministic path. That blurs the agent/CLI boundary and should not remain active in the target architecture.

### 2. Require Explicit SourceNeed For Product Search

Target behavior:

- production source search is driven by agent-selected `SourceNeed`
- `build_advisor_queries(snapshot, source_need=...)` remains the active path
- remove or archive `build_advisor_queries(snapshot)` without a source need
- product-facing tests assert that status-driven query generation is not used by turn flow

Why:

Snapshot readiness can produce stale or irrelevant retrieval. Source search should happen only after the agent decides the current turn needs source support and chooses the retrieval objective.

### 3. Add Agent-Adjudicated Focus Coverage

Target behavior:

- focus-term concept coverage is judged by an agent or human reviewer
- each judgment records rationale
- CLI scorer aggregates recorded judgments

Proposed artifact shape:

```json
{
  "case_id": "sourceneed_v1_010",
  "adjudicator": "agent",
  "judgments": [
    {
      "expected_concept": "get leads to engage",
      "actual_terms": ["front-end offer", "engagement", "STR owners"],
      "covered": true,
      "rationale": "Engagement captures the intended lead-engagement concept in the user turn."
    }
  ]
}
```

### 4. Add Agent-Adjudicated Chunk Usefulness

Target behavior:

- retrieved chunk usefulness is judged by an agent or human reviewer
- each judgment records rationale
- query-quality reports separate known-useful seed labels from adjudicated chunk usefulness

Artifact shape:

```json
{
  "case_id": "query_v1_010",
  "source_need": {
    "intent": "recommendation_evidence",
    "layers": ["offers"],
    "focus_terms": ["front end offer", "get leads to engage"]
  },
  "chunk_judgments": [
    {
      "chunk_id": "attraction-offers:2",
      "useful": true,
      "rationale": "The chunk directly explains the front-end offer mechanism."
    }
  ]
}
```

## Order Of Operations

### Phase 1: Boundary Repair

1. Define the product command contract for turn persistence.
2. Stop product-facing `chat`/turn flow from auto-planning or searching without an explicit source need.
3. Add a concrete source-need search surface, preferably `search --source-need-json ...`.
4. Remove or archive status-driven query generation.
5. Update tests so product-facing query construction requires explicit `SourceNeed`.
6. Adjust the advisor skill and operating guide so agents call `search` only after generating a source need.

### Phase 2: Eval Meaning Repair

1. Add semantic adjudication artifact schema for focus-term coverage.
2. Run agent adjudication on current source-need partial cases.
3. Update source-need reports to separate:
   - deterministic debug metrics
   - agent-adjudicated semantic metrics
4. Add semantic adjudication artifact schema for retrieved chunk usefulness.
5. Run chunk usefulness adjudication on the current query-quality cases.
6. Update query-quality reports to separate:
   - known-useful seed-label metrics
   - adjudicated chunk-usefulness metrics
7. Only then revisit retrieval-backend comparisons.

## Acceptance Criteria

- Product-facing source search has an explicit `SourceNeed`.
- Product-facing turn flow does not call `build_advisor_queries(snapshot)` without a `SourceNeed`.
- Tests assert status-driven query generation is removed, archived, or not used by product flow.
- A source-backed trace records `source_need`, query, returned chunks, and cited chunk IDs.
- No active narrative treats `build_advisor_queries(snapshot)` fallback as production behavior.
- `chat` is removed from product-flow docs or replaced by `turn record`.
- Source-need report includes recorded semantic coverage judgments or clearly marks exact focus recall as debug-only.
- Query-quality report includes recorded chunk usefulness judgments before being used for retrieval-backend selection.
- Unit tests and smoke evals pass.

## Non-Goals

- Do not add external model-service calls.
- Do not build a hosted vector DB.
- Do not build a web UI.
- Do not replace the agent with deterministic routing rules.
- Do not expand into large benchmarks before the boundary is corrected.
