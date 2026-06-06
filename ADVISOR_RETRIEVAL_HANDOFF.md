# Advisor Retrieval Handoff

This note records the current retrieval behavior, the 1584 Design trace review, and the next professional design move. It exists so another agent can continue the work without replaying the conversation.

## Current Goal

The project is a hiring artifact for an AI engineering role. BM25-only retrieval is acceptable as a baseline, not as the final candidate architecture if the job description expects embeddings, cached vectors, hybrid retrieval, or cost-aware RAG design.

The final write-up should show:

- traceable source-grounded advisor turns
- next-action classification from conversational state
- search-query construction only after the agent chooses source-material search
- cached business context in `BusinessSnapshot`
- cached corpus embeddings or a local vector index for semantic retrieval
- BM25 versus dense versus hybrid comparison under the same eval harness
- clear logs showing why retrieval happened, which query ran, and which chunks were used

The immediate dev requirement is to improve two separate capabilities:

1. Next-action classification: the agent should classify whether the current turn needs source-material search, saved snapshot/log lookup, local business-doc inspection, deterministic calculation, clarification, or direct answer synthesis.
2. Search-query quality: only when source-material search is the right action, the agent should build a focused query that retrieves useful Money Models chunks.

Do not evaluate query quality on turns where source-material search should not have happened.

Next-action classification should be improved through iterative skill and tool-surface testing: write clearer skill instructions, run realistic conversations, inspect logs, identify wrong action labels, and revise the skill or CLI affordance that caused the mistake. The target is not a deterministic keyword router.

Search-query quality needs its own improvement loop:

1. Start with only turns where source-material search is the expected action.
2. Label the expected retrieval purpose: concept teaching, diagnostic explanation, comparison, or recommendation support.
3. Label expected layer and focus terms, not exact query strings.
4. Generate short source-seeking queries from the current turn plus compact snapshot context.
5. Inspect returned chunks and revise query construction examples/templates when the query retrieves broad, stale, or irrelevant material.
6. After this is stable, compare BM25, dense, and hybrid retrieval on the same search-appropriate turns.

## What Is Logged

Each saved session turn under `.money-model-advisor/sessions/*.json` records:

- `user_message`
- `actions`
- `retrieval_queries`
- `evidence`
- `assistant_message`
- final `snapshot`

For retrieval, `retrieval_queries` saves:

- `intent`
- `layer`
- exact `query`
- `reason`

`evidence` saves the returned chunks for that query:

- chunk `id`
- `chapter`
- primary `layer`
- all `layers`
- score
- preview

This is enough to audit which query generated which chunks on each turn.

## 1584 Design Trace Review

Reviewed context directory:

```text
/Users/benjaminmackenzie/1584_design
```

Recent conversation turns reviewed:

| Time | User turn | Retrieval |
|---|---|---|
| `22:45:44Z` | "let's talk about money models" | none |
| `22:46:39Z` | referral partner CAC / Google Business Profile leads | none |
| `22:48:23Z` | upfront payment / services and pricing lookup | none |
| `22:48:51Z` | "that works as an average" | none |
| `22:49:18Z` | "why do we need fulfillment cost" | none |
| `22:51:02Z` | "let's call fulfillment cost $3k" | diagnostic source retrieval |
| `22:51:30Z` | "what happened to the $1k we pay to referral partners" | same diagnostic source retrieval |
| `22:52:01Z` | "ok, so where does this leave us" | same diagnostic source retrieval |
| `22:52:52Z` | "let's explore how much we can spend on ads if we run them" | same diagnostic source retrieval |

The repeated retrieval query was:

```text
CAC first 30 day gross profit payback period client financed acquisition gross profit
+ business type
+ ICP
+ core offer description
```

Returned chunks:

| Chunk | Layer | Why it appeared |
|---|---|---|
| `cfa:0` | `unit-economics` | CAC, gross profit, payback, client-financed acquisition |
| `money-models-offer-stacks:0` | `offers` plus cross-tags | broad money model / offer stack overview |
| `how-businesses-make-money:2` | `unit-economics` | the three numbers: CAC, gross profit, payback period |

These chunks are directionally reasonable for CAC/payback explanation. The issue is not the chunks themselves; it is the next-action and query policy.

## Senior Critique

The current retrieval trace is useful, but the next-action classifier and query generator are immature.

Main failure mode:

```text
snapshot becomes diagnosable
→ every later turn triggers the same diagnostic retrieval
→ retrieval ignores the specific current conversational need
```

Concrete problems:

- Query generation is too state-triggered. It keys off `advisory_status = diagnosable` more than the current user turn.
- Query strings are bloated with long business descriptions. This can dilute the actual source-material need.
- The same query repeats for concept questions, saved-context questions, summary questions, and ad-spend questions.
- The turn "why do we need fulfillment cost" probably should retrieve unit-economics source support about gross profit and payback, but retrieval did not happen.
- The turn about "services and pricing" should be logged as business-doc lookup, not Money Models source retrieval.
- The turn "what happened to the $1k we pay to referral partners" should primarily inspect saved snapshot/provenance, not repeat corpus retrieval.
- The ad-spend turn should generate an advertising/CFA query, not reuse the generic payback query.

Vector retrieval will not fix this by itself. Bad next-action classification and bad query planning remain bad with a vector DB.

## Desired Tool Planner

Separate the advisor's next action before constructing retrieval queries:

| Need | Source/tool |
|---|---|
| Missing business fact | ask user or inspect local business docs |
| Business-doc lookup | agent file inspection, then `update_snapshot` |
| Saved fact/provenance lookup | `read_snapshot` / `logs` |
| Calculation | `calculate` or deterministic snapshot math |
| Concept teaching | Money Models source search |
| Diagnostic explanation | Money Models source search plus calculation |
| Recommendation support | Money Models source search focused on the proposed fix |

Then build source-material queries from:

- current user turn
- advisor-selected intent
- short focus terms
- compact snapshot context

Avoid dumping long business descriptions into every query. Use short terms such as:

```text
STR interior design
high-ticket service
CAC
first 30 day gross profit
payback period
client-financed acquisition
```

## Retrieval Design Direction

Current implementation:

- BM25-style local search over heading-aware chunks
- good enough as a transparent baseline
- not enough as the final JD-aligned retrieval architecture

Recommended candidate architecture:

1. Keep BM25 as the lexical baseline.
2. Add local cached embeddings for transcript chunks.
3. Add dense retrieval over the cached vectors.
4. Add hybrid retrieval combining BM25 and dense scores.
5. Compare BM25, dense, and hybrid under the same turn-level eval set.
6. Keep retrieval traces in session logs.

Vector DB note:

- A hosted vector DB is not necessary for the current transcript corpus.
- A local vector index is enough for the portfolio build and better aligned with the no-external-model-service runtime.
- Good local options include FAISS, Chroma, or LanceDB.
- The important JD signal is cached embeddings plus evaluated semantic/hybrid retrieval, not a hosted database for its own sake.

## Next Implementation Step

Build a small next-action classification eval and query-quality eval before adding dense retrieval:

1. Create a turn-level eval set from the 1584 conversation.
2. Label expected action per turn: no retrieval, business-doc lookup, snapshot/provenance lookup, calculate, clarify, direct answer, or source-material search.
3. Score next-action classification first: did the agent choose the right kind of action?
4. For source-material turns only, label expected query intent/layer/focus terms.
5. Score search-query quality second: did the query retrieve useful source chunks?
6. Update the skill/CLI planner behavior so retrieval is chosen by advisor need, not only snapshot readiness.
7. Add local cached embedding index and compare retrieval variants after tool planning and query construction are less blunt.

The write-up should describe the current BM25 traces as baseline instrumentation, not as final retrieval quality.
