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

## Trace Recorder

A trace recorder is the eval tool or workflow that captures what happened during a case and writes it into a structured artifact such as `run.json`.

For this project, the trace recorder should:

- set up the isolated eval directory
- copy fixtures into place
- capture commands, file reads, logs, stdout, stderr, snapshot hashes, and final answer text
- record observable action evidence in `actual_actions[]`

The trace recorder should not decide which advisor action to take. If it chooses actions from the expected label, it becomes a deterministic planner and stops measuring the agent's judgment.

## Deterministic Planner

A deterministic planner is code that chooses the next action from fixed rules or case labels.

Example:

```text
if required_actions contains read_snapshot:
    run snapshot command
```

That can be useful in some systems, but it is wrong for the v1 next-action eval because the thing being evaluated is whether the skill-guided agent chooses the right next action.

## Acting Agent

The acting agent is the agent being evaluated. It receives the case context, uses the skill and CLI, and decides what to do next.

The acting agent should not see the expected labels for the case.

## Trace Extractor

The trace extractor maps observable evidence into `actual_actions[]`.

Example:

```text
snapshot CLI command -> read_snapshot
search command or retrieval_queries entry -> search_source_material
```

The extractor should mark weak evidence as `inferred` or `missing` instead of pretending it is direct.

## Fanout

Fanout is the number of retrieval calls created from one user-facing source search.

In this project, fanout can come from two places:

- query variants: one `SourceNeed` may use 2-4 query strings instead of one
- namespaces: one query may search one or more selected vector namespaces

Example: a source need with 4 query variants and 2 target namespaces creates 8 vector searches. Fanout is not automatically bad: it can improve recall because the system asks the corpus from several angles. It becomes a problem when extra searches add latency, cost, or noisy candidates without improving quality. For hosted Pinecone runs, fanout should be measured and usually bounded or parallelized.

## Scorer

The scorer compares the extracted `actual_actions[]` against the case labels.

In this repo, that is `scripts/eval_tool_use_judgment.py`.

## Source Need

The source need is the specific kind of Money Models source support the advisor needs for one source-material search call.

It is narrower than the user's whole business situation and narrower than the full answer plan. For example, if the user asks, "why do we need fulfillment cost to know whether ads can work?", the source need is not "1584 Design, STR owners, diagnostics, pricing, and ads." The source need is "explain gross profit, CAC, and payback period."

The source need is used only after the advisor has already decided that source-material search is the right tool.

One advisor turn may need more than one source need. In that case, the planner should issue multiple source-material searches, each with its own source need, instead of putting multiple intents into one source need.

## Acceptable Intents

Acceptable intents are eval-only labels for source-need generation cases where more than one primary retrieval objective is defensible.

They do not change the runtime contract. A runtime source need still emits one `intent` for one search call. Acceptable intents only prevent the scorer from marking a reasonable primary intent wrong when the user turn naturally straddles two purposes, such as teaching a concept and recommending whether it applies.

## Source-Specific Query

A source-specific query is a local corpus-search query centered on the current source need.

Good example:

```text
gross profit CAC payback fulfillment cost first 30 days
```

Bad example:

```text
premium interior design STR owner diagnostic CAC payback attraction offer upsell
```

The bad example is too broad because it stuffs business context and unrelated Money Models concepts into one search. That can retrieve plausible chunks while missing the material the advisor actually needs to cite.

## Focus Terms

Focus terms are the few concepts that should be preserved in a source-specific query.

They are not exact keyword labels that the final answer must contain. They are a lightweight way to check whether the query is aimed at the right source need.

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
- trace parse rate
- inferred-action count
- failures by turn type
- stale-query reuse count
- unlogged-action count

Diagnostic metrics are still valuable. They just should not be presented as the headline result.

## Trace Parse Rate

Trace parse rate is the percent of eval cases where the evaluator can extract an action trace at all.

If the trace cannot be parsed, the report cannot confidently say what the agent did.

## Trace Directness Rate

Trace directness rate is the percent of actual actions supported by direct evidence.

Example direct evidence:

- a CLI command in `run.json`
- a `retrieval_queries` entry in a session file
- a snapshot update event

A low trace directness rate means the evaluator is relying too much on inference.

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
- missed state lookup
- premature clarify
- premature recommendation
- missed calculation
- missed diagnosis
- stale query reuse
- forbidden action
- unlogged action
- materially wrong first action
- state contamination

This makes eval reports more useful than a single accuracy number.

Common failure types:

| Failure type | Meaning |
|---|---|
| `false_search` | The agent searched source material when search was forbidden. |
| `missed_search` | Source-material search was required but absent. |
| `wrong_state_tool` | The agent used the wrong state source, such as local docs instead of snapshot/logs. |
| `missed_state_lookup` | The case required saved-state lookup, but the agent did not inspect saved state. |
| `premature_clarify` | The agent asked a question even though the needed fact was available. |
| `premature_recommendation` | The agent recommended before required facts, calculation, or source support were available. |
| `missed_calculation` | Calculation was required but absent. |
| `missed_diagnosis` | Diagnosis was required but absent. |
| `stale_query_reuse` | The agent reused a generic or previous search query that did not match the current turn. |
| `forbidden_action` | Any action listed as forbidden happened. |
| `wrong_first_action` | The first action was wrong or materially harmful, even if later actions recovered. Harmless context-loading before the required action should be adjudicated, not automatically counted as this failure. |
| `unlogged_action` | The action may have happened, but the trace does not prove it. |
| `state_contamination` | The result depends on state not present in the fixture. |
