# Glossary

Plain-English definitions for the terms used in this repo.

## Trace

A trace is the record of what happened during one run or one advisor turn.

For this project, a trace should let a reviewer answer:

- what the user asked
- what saved business context existed at the time
- what action the agent chose
- what CLI commands or tools ran
- whether source material was searched
- what query was used, if search happened
- what chunks came back, if search happened
- what answer was produced
- where the raw evidence for the run is saved

Example:

```json
{
  "case_id": "tooluse_v1_001",
  "user_turn": "what happened to the $1k referral partner number?",
  "actual_actions": ["read_snapshot"],
  "forbidden_actions": ["search_source_material"],
  "session_path": "evals/runs/next_action/baseline/tooluse_v1_001/session.json",
  "trace_confidence": "direct"
}
```

A trace is not the same thing as the final answer. The final answer is only one output inside the trace.

## Trace Confidence

Trace confidence describes how clearly the trace proves that an action happened.

| Value | Meaning |
|---|---|
| `direct` | The action is explicitly logged, such as a search query or CLI command. |
| `inferred` | The action is implied by the answer or side effects, but not directly logged. |
| `missing` | The run does not give enough evidence to classify the action. |

Direct evidence is strongest. Inferred evidence is useful for debugging, but should be reported honestly.

## Next-Action Classification

Next-action classification is deciding what the agent should do next.

Example labels:

- `clarify`
- `update_snapshot`
- `read_snapshot`
- `read_logs`
- `inspect_local_docs`
- `calculate`
- `diagnose`
- `search_source_material`
- `compose_answer_from_state`
- `answer_without_tool`

This is separate from query generation. First decide whether search is the right next action. Only then generate a search query.

`compose_answer_from_state` means the answer is synthesized from already-available conversation, snapshot, calculation, or diagnosis state.

`answer_without_tool` means no state read, calculation, mutation, diagnosis, or retrieval is needed.

## Query Generation

Query generation is creating the search text sent to the Money Models source corpus.

Example:

```text
client financed acquisition CAC payback first 30 day gross profit
```

Query generation only matters when the next action is `search_source_material`.

## Source Material

Source material means the Money Models transcript chunks in this repo's corpus.

It does not mean:

- the user's local business docs
- the web
- prior conversation logs
- the saved `BusinessSnapshot`

## Source-Material Search

Source-material search means using the local corpus search tool to retrieve Money Models chunks that can support an answer with citations.

In the CLI this is:

```bash
money-model-advisor search ...
```

## Chunk

A chunk is a searchable section of the Money Models transcripts.

The corpus is too large to search as one giant document, so it is split into chunks. Retrieval returns chunk IDs, previews, scores, and metadata.

## Retrieval

Retrieval means finding relevant chunks from the Money Models source corpus.

Current baseline retrieval is BM25-style local search. Future retrieval experiments may include cached local embeddings, dense retrieval, and hybrid retrieval.

Retrieval is not the same as next-action classification. Retrieval happens only after the agent has decided that source-material search is needed.

## BM25

BM25 is a classic keyword-based ranking method.

It tends to work well when the query and the source use similar words. It is a good transparent baseline, but it can miss semantic matches where the wording differs.

## Dense Retrieval

Dense retrieval uses embeddings, which are vector representations of text meaning.

Dense retrieval can find conceptually similar chunks even when the exact words differ. In this project, any dense retrieval should use cached/local embeddings rather than external model-service calls.

## Hybrid Retrieval

Hybrid retrieval combines lexical search, such as BM25, with dense retrieval.

The goal is to get the benefits of both:

- BM25 for exact terms and framework names
- dense retrieval for paraphrases and semantic matches

## Embedding

An embedding is a vector representation of text.

Texts with similar meanings should have nearby vectors. Embeddings can be cached so the same corpus does not need to be re-embedded repeatedly.

## Cached Embeddings

Cached embeddings are saved vectors for corpus chunks.

Caching matters because it saves time, compute, and cost. In this project, cached embeddings are part of the intended retrieval architecture, but external model-service calls are not part of the active runtime.

## BusinessSnapshot

`BusinessSnapshot` is the saved structured context for a business.

It stores accepted facts such as:

- business type
- ICP
- core offer
- CAC
- first-30-day gross profit
- gross margin
- money-model stack

The snapshot is a cache for business context so the agent does not need to reread local business docs every turn.

## Local Business Docs

Local business docs are the user's files about the business.

The agent may inspect them when context is missing, then save accepted facts into the `BusinessSnapshot`. The Money Models source search does not search these docs.

## Run Protocol

Run protocol means the exact steps for executing an eval case.

It should specify:

- which case is being run
- what business directory is used
- what snapshot fixture is loaded
- what command or agent workflow runs
- where raw outputs and session logs are saved
- how the run maps back to the case ID
- what action trace was recorded

The run protocol prevents eval cases from becoming impossible to reproduce.

## Fixture

A fixture is prepared test data used to make an eval case repeatable.

Examples:

- a snapshot JSON file
- a small local business-doc directory
- a prior conversation log

Fixtures help prevent test cases from contaminating each other.

## State Contamination

State contamination happens when one eval case changes saved state in a way that affects another case.

Example: case 1 writes CAC into the snapshot, then case 2 accidentally uses that value even though its fixture did not include CAC.

The fix is to use fresh eval directories or explicitly reset state for each case.

## Dev / Regression / Scenario Holdout

These are eval splits.

| Split | Meaning |
|---|---|
| `dev` | Cases used while improving the system. |
| `regression` | Cases for bugs we already found and want to prevent from returning. |
| `scenario_holdout` | Untouched cases from the same scenario, used as a small sanity check after changes. |

For this portfolio project, `scenario_holdout` is not a production-grade generalization test. A production eval would add a cross-business holdout.

## Required / Allowed / Forbidden Actions

These fields define how a next-action classification case is scored.

| Field | Meaning |
|---|---|
| `required_actions` | Actions that must happen for the case to pass. |
| `allowed_actions` | Actions that are acceptable but not required. |
| `forbidden_actions` | Actions that should not happen. |

This is better than one exact label because some turns reasonably involve more than one action.

## False Search

A false search happens when the agent searches the Money Models source corpus even though search was forbidden for that case.

Example: the user asks what number they gave earlier, and the agent searches source material instead of reading saved state or logs.

## Missed Search

A missed search happens when source-material search was required but the agent did not search.

Example: the user asks for a source-grounded explanation of client-financed acquisition, and the agent answers without retrieving source material.

## Headline Metrics

Headline metrics are the main numbers we would put in the project write-up or summary table.

They are the scores we are comfortable using to support the core claim.

Example:

```text
Next-action classification false-search rate fell from 40% to 0% on regression cases.
```

For this project, headline metrics should be based on direct trace evidence whenever possible. If an action is only inferred from prose, it can still be useful, but it should not quietly drive the main score.

## Diagnostic Metrics

Diagnostic metrics are supporting numbers used to understand failures.

They help answer "what went wrong?" but they are not the main claim.

Examples:

- trace directness rate
- inferred-action count
- failures by turn type
- stale-query reuse count
- unlogged-action count

Diagnostic metrics are still valuable. They just should not be presented as the headline result.

## Label

A label is the expected classification for an eval case.

In this project, labels are policy-conformance labels: they say what the Money Model Advisor is supposed to do under the documented design.

They are not claims about what every possible assistant must do.

## Labeling Guide

A labeling guide is a short set of rules and examples that explains how labels should be assigned.

It helps reviewers apply labels consistently, especially for ambiguous cases.

## Ambiguity

Ambiguity describes how many reasonable action paths a case has.

| Level | Meaning |
|---|---|
| `low` | One action path is clearly right. |
| `medium` | More than one path is reasonable; allowed actions matter. |
| `high` | Too open-ended for headline scoring; discuss qualitatively. |

## Failure Taxonomy

A failure taxonomy is a list of failure types used in reports.

Examples:

- false search
- missed search
- wrong state tool
- premature clarify
- premature recommendation
- stale query reuse
- unlogged action
- correct action but wrong first action

This makes eval reports more useful than a single accuracy number.
