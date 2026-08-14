# Building a Money Model Advisor

This is the canonical narrative for the current project direction.

The target hiring context is recorded in `JOB_DESCRIPTION.md`. This project is intended to demonstrate the skills in that role: production-grade agent workflows, tool use, RAG pipeline judgment, golden datasets, retrieval metrics, cached embeddings, cost-aware design, observability, and regression-oriented iteration.

The product is an agent-operated advisor for Alex Hormozi's *$100M Money Models*. It helps a founder diagnose unit economics, understand the money-model stack, compare concepts, and choose the next practical change to test. A human talks to an agent; the agent follows the project skill's guidance; the agent runs the local CLI against saved local state. External model APIs are not used for agent planning, labeling, answer synthesis, or acting-agent eval work. Embedding APIs and Pinecone are allowed for deterministic retrieval infrastructure.

## Corrected Product Frame

The advisor is not a one-shot retrieval bot. A realistic user starts with a conversational goal:

- "Help me build a money model."
- "I think CAC is too high."
- "Our offer works, but cash is tight."
- "What should I add after the first sale?"
- "Explain rollover upsells in my situation."

Those are different advisory moves. The system should maintain a structured `BusinessSnapshot`. The agent inspects local business docs as needed, saves accepted facts to the snapshot, uses deterministic CLI tools for calculations and source search when appropriate, composes the answer, then records the completed turn. Advisory turns should not depend on deterministic `chat` synthesis as the advisor brain.

The v1 runtime is:

```text
human asks agent for advice
→ agent follows Money Model Advisor skill guidance
→ agent inspects local docs if snapshot context is missing
→ agent saves accepted facts to BusinessSnapshot
→ agent runs local CLI commands for calculation, source search, and trace logging
→ agent answers with cited source chunks when support is needed
→ agent records the completed turn with turn metadata
```

No external model-service call is part of the active advisor runtime.

## Corpus And State

The source corpus is transcribed into `corpus/transcripts/`, one lesson per file. The corpus naturally separates into five layers:

| Layer | Purpose |
|---|---|
| `unit-economics` | CAC, gross profit, payback period, CFA, diagnostic math |
| `offers` | attraction offers and front-end offer types |
| `upsells` | post-sale monetization and premium options |
| `downsells` | save offers, payment plans, lower-friction alternatives |
| `continuity` | recurring offers, retention, discounts, continuity bonuses |

The key runtime object is `BusinessSnapshot`, defined in `BUSINESS_SNAPSHOT_V1.md`. It stores accepted business facts, source metadata, calculated economics, missing fields, and advisory status. It is the cache for business context. The agent may inspect local docs before updating the snapshot. Product-facing advisor flow should use the snapshot, not crawl local business files every turn.

## Chunking Decision

The adopted strategy is `framework-aware`: preserve transcript headings, split long sections at framework cues, and use bounded overlapping windows as a fallback.

The original 32-case BM25 screen could not distinguish it from heading-aware. Revalidation on the active 46-case, single-query hybrid path did: both reached 93.5% Hit@1 and 100% Hit@5, while framework-aware improved Useful@5 from 73.0% to 78.7% and reduced the largest chunk from 2,471 to 922 words. Fixed-800 reached 95.7% Hit@1 but returned 51% more text across the top five.

Reports: `evals/reports/chunking_comparison.md` and `evals/reports/active_query_chunking_revalidation.md`.

## Retrieval Position

The active retrieval path is local corpus search over transcript chunks. Retrieval means: search the Money Models source corpus for chunks that can support the advisor's answer with citations.

It does not mean:

- searching the web
- rereading local business files
- deciding the user's intent
- calling external model services

The active product path uses one corpus-guided query through unfiltered hybrid search over framework-aware chunks. BM25 is retained as the lexical control. Cached embeddings and the local/Pinecone vector-store boundary keep retrieval execution deterministic and repeatable.

The next retrieval work is not just "write better queries." The advisor must pass two gates:

1. Tool-use judgment: decide whether the current turn needs source-material search at all, versus snapshot/log lookup, local business-doc inspection, calculation, clarification, or direct answer synthesis.
2. Search-query quality: when source-material search is the right tool, build a source-specific query that retrieves useful Money Models chunks.

Query quality should be evaluated only on turns where source-material search is actually the right action.

This order matters. The tool-use suite tests when to search; the 46-case query suite tests what query to write and how to retrieve with it. Keeping those risks separate prevents a retriever comparison from being dominated by wrong-tool or generic-query failures.

The early chapter-level control was:

| Retriever | Hit@1 | Hit@5 | MRR |
|---|---:|---:|---:|
| BM25 heading-aware | 81.25% | 100.00% | 0.8917 |

Report: `evals/reports/local_retrieval_baseline.md`.

## Evaluation Philosophy

The project is still experiment-first, but all active experiments must run locally or through agent-assisted human review. The point is to demonstrate clear engineering judgment, not to accumulate fragile experiments.

`GOLDEN_DATASET.md` maps the case files, scorers, reports, current results, and decisions.
The active suite covers tool-use judgment, current source-event logging, query quality,
chunking, retrieval and embedding choices, calculation integrity, and seed answer
quality. Retired source-need and multi-query cases remain historical evidence.

Core design principle: the agent judges meaning; the CLI handles deterministic bookkeeping. The advisor is built around an agent that can read conversation context, inspect local docs, decide which tool is appropriate, write a corpus-guided search request, and adjudicate semantic quality. The CLI should not pretend to be that semantic judge. Its job is to persist state, run formulas, execute local search, capture traces, and score recorded judgments. The detailed CLI product contract is defined in `CLI_DESIGN.md`.

This means deterministic code is appropriate for:

- snapshot schema, persistence, and source metadata
- unit-economics calculations
- numeric/accounting state classification after the agent has chosen the task
- local corpus search execution
- exact trace capture and report generation
- validation that recorded eval artifacts have the expected shape

Agent judgment is appropriate for:

- deciding the next advisory action
- writing one corpus-guided `SearchRequest.query`
- judging whether retrieved chunks actually support a claim
- judging whether focus terms are conceptually covered even when wording differs
- adjudicating ambiguous intent/layer cases
- evaluating final answer quality, grounding, and usefulness

The system should record those agent judgments as auditable artifacts, with rationale, instead of burying semantic decisions in brittle keyword rules.

Senior audit refinement: deterministic code can classify numeric/accounting states such as "CAC is not recovered by first-30-day gross profit." That is not the same as deciding the user's conversational intent. The agent decides whether the current turn needs search and writes the query from the question, saved business facts, and corpus guide.

Active eval assets:

| Asset | Purpose |
|---|---|
| `evals/golden.jsonl` | pilot query set for local retrieval smoke checks |
| `evals/realistic_queries.jsonl` | more realistic user-intent query draft |
| `evals/obligations.jsonl` | reviewed required-claim support labels |
| `scripts/eval_smoke.py` | deterministic correctness smoke suite |
| `scripts/eval_retrieval.py` | local retrieval baseline report |
| `scripts/compare_chunking.py` | chunking comparison |
| `scripts/audit_query_realism.py` | lexical-overlap audit for query realism |
| `scripts/review_obligations.py` | local review UI for required-claim labels |
| `scripts/score_obligation_support.py` | required-claim support scorer |
| `evals/advisor_tool_use_cases.jsonl` | product-behavior cases for next-action classification |
| `scripts/capture_tool_use_trace.py` | strict trace recorder for isolated next-action eval runs |
| `scripts/eval_tool_use_judgment.py` | next-action classification scorer and report generator |
| `evals/advisor_search_decision_cases.jsonl` | balanced search/no-search cases across five business contexts |
| `scripts/eval_search_decision_models.py` | isolated semantic search-gate model comparison |
| `evals/advisor_search_query_cases.jsonl` | search-appropriate turns for source-query quality |
| `scripts/eval_search_query_quality.py` | source-query quality scorer and report generator |
| `scripts/compare_retrieval_backends.py` | BM25/vector/hybrid comparison after source-need generation passes its seed gate |

For next-action classification, the project uses a trace recorder rather than a deterministic planner. The recorder prepares isolated eval directories, copies fixtures, hides expected labels from the acting agent, captures observable workflow evidence, and writes `run.json`. It does not choose the advisor's next action. That separation matters because the eval subject is the skill-guided agent's judgment, not a hard-coded runner.

The trace design separates three roles:

- the acting agent performs the case using the skill and local CLI
- the trace extractor maps commands, logs, file reads, session fields, and snapshot diffs into `actual_actions[]`
- the scorer compares `actual_actions[]` against the case labels

This prevents self-report from becoming the metric and keeps weak evidence visible as `inferred` or `missing`.

Reference-trace result: all 24 cases have completed trace artifacts and the scorer reproduces the expected action sequences. This validates the cases and scorer; operating-model search decisions are measured separately below.

## Historical Retrieval Experiments

The SourceNeed, subject-filtering, and multi-query material below records the path to
the current design. Those schemas remain only for reproducibility and compatibility;
they are not the active product contract. The superseding decision is the single
corpus-guided `SearchRequest.query` described below.

Historical source-query result: the earlier golden search-query slice covered 30 search-appropriate turns. Reference mode used reviewer-authored source-specific queries. Generated mode passed an explicit advisor-selected `SourceNeed` into the runtime query builder, and generated-variants mode added constrained query variants. These results explain the design path but do not define the current one-query contract.

Historical source-need result: `evals/advisor_source_need_cases.jsonl` contains 14 seed cases from the retired taxonomy-based planner. Its traces and report remain available for reproducibility, but `SourceNeed` no longer drives product retrieval.

The system supports BM25, vector, and hybrid over the same framework-aware chunks. Vector search uses OpenAI embeddings only for deterministic vectorization, not for agent judgment or answer synthesis. Embeddings are cached under `.cache/embeddings/`; hybrid uses reciprocal-rank fusion over BM25 and vector rankings.

The historical backend and multi-query results are preserved in
`evals/reports/retrieval_backend_comparison.md` and its companion reports. They
established runnable vector and hybrid paths, but the current decision comes from the
later 46-case one-query matrix below.

## Current Retrieval Decision

Superseding query-generation decision (updated 2026-08-12): the fixed-variant result above is retained as historical downstream-retrieval evidence, not the active product method. A later controlled experiment started from the real user question and saved snapshot, hid reviewer fields, removed subject filters, and compared raw question, unguided rewrite, and corpus-guided rewrite with exactly one query each. Every saved query was evaluated unchanged through BM25 and hybrid over the final framework-aware chunks. Across the 46-case audited regression suite, corpus-guided `gpt-5.5` hybrid retrieval reached 93.5% Hit@1, 97.8% Hit@3, 100.0% Hit@5, and 78.7% Useful@5, versus 63.0%/80.4%/87.0%/50.9% for the raw question and 80.4%/91.3%/93.5%/62.6% for the unguided rewrite. Corpus guidance remained the strongest approach under BM25, while hybrid preserved 100% Hit@5 and improved Useful@5 over BM25 under both guided query writers. The runtime uses one `SearchRequest.query` authored from the same versioned guide, executes it unfiltered through hybrid, and rejects trace/query mismatches. Codex performed the semantic relevance audits rather than an independent human reviewer, which is recorded as a benchmark limitation. See `evals/reports/active_framework_retrieval_matrix.md`.

Embedding-model decision (2026-08-13): after freezing query generation, chunks, hybrid retrieval, and top five, `text-embedding-3-small` was compared with `text-embedding-3-large` at Pinecone's deployable 1,536 dimensions. The predefined rule required Large to preserve Hit@5 and improve Useful@5 by at least two points or mean rank by 0.10. After reviewing all 39 new case-passage pairs, Large preserved 100% Hit@5, raised Useful@5 from 78.7% to 86.5%, and reduced Noise@5 from 21.3% to 13.5%. Its estimated uncached cost for all 204 chunks and 46 queries was $0.017 versus $0.003. Large is now the runtime default. Report: `evals/reports/embedding_model_comparison.md`.

BM25 is the lexical control. The selected architecture is one agent-authored,
corpus-guided `SearchRequest.query` through unfiltered hybrid retrieval over cached
lexical and vector candidates. The vector-store boundary lets local evaluation and
Pinecone use the same retrieval interface.

Historical Pinecone parity result: the corpus was indexed into Pinecone as 202 heading-aware chunk vectors using stable ids and citation metadata. The older 30-case multi-query slice is retained for history, but it no longer defines the runtime benchmark.

The Pinecone run exposed a deployment tradeoff rather than a quality regression. The original hosted eval executed query variants sequentially, producing 120 Pinecone vector searches across 30 cases and p50 retrieval above 5s. After adding bounded per-case parallel retrieval (`--max-workers 8`), the same full 30-case Pinecone single-namespace benchmark completes successfully: hybrid+variants reaches 100.0% Hit@3, 100.0% Hit@5, mean known-useful rank 1.17, p50 retrieval about 1.43s, p95 about 1.76s, 120 vector searches, 100.0% query embedding cache hits, and zero embedding API batches. This should not be hidden in the write-up. The correct interpretation is: Pinecone proves the hosted vector-storage path and preserves retrieval quality, while production optimization should continue to bound query fanout, tune top-k, parallelize safely, and add request-level observability before claiming final latency readiness.

Historical Pinecone namespace result: the older 30-case multi-query workload also found no quality reason to adopt subject namespaces. Its counts and latency figures are retained only for reproducibility; the active-path result below supersedes them.

In that historical workload, all 90 (case, retriever) rows had identical top-five order across the two layouts.

That older workload measured query-variant fanout rather than one current product request, so its latency figures are historical.

One caveat on scope: this eval slice is saturated. Hit@5 is 100% for every backend in every condition, and BM25 alone reaches 96.7% Hit@3, so the slice has no headroom to detect a quality improvement from anything. The supported claim is "no measurable difference on this slice," not "namespaces never help." If the corpus grows to the point where layers genuinely interfere in ranking, re-test with a harder slice before revisiting this decision.

Decision: five-layer namespaces are implemented and verified, but they are not a better v1 default than single namespace plus metadata filtering on this evaluation slice. The senior product choice is to keep namespace support available for index-management and future scale, skip a runtime agent namespace-selection eval for now, and use the simpler single-namespace path by default until namespace routing shows a measured quality or latency win.

Superseding active-path result (updated 2026-08-13): the first Pinecone run exposed a redundant 10x over-fetch: hybrid consumed 25 vector candidates but requested 250. Removing it preserved every Small-model top-five list. The selected Large 1,536-dimension vectors were then indexed in an isolated namespace and all 46 frozen queries were replayed sequentially. The hosted path reached 93.5% Hit@1, 100% Hit@5, 86.1% Useful@5, 1.13s p50, and 1.43s p95. The earlier oracle subject split had not improved quality, so the active path remains one unfiltered namespace. Reports: `evals/reports/pinecone_candidate_depth_optimization.md` and `evals/reports/pinecone_large_embedding_revalidation.md`.

Reranking decision: the current hybrid retriever uses reciprocal-rank fusion to combine
BM25 and vector rankings. No separate learned reranker has been adopted. Revisit that
choice if a broader golden suite shows useful passages entering the candidate pool but
regularly missing the returned top five.

Search-gate model result (2026-08-13): `scripts/eval_search_decision_models.py` isolates the semantic decision from shell use, retrieval, and answer writing. The deterministic harness loads current advisor state, recent turns, and local documents, then each model makes one blind search/no-search decision on 48 frozen cases. `gpt-5.5` scored 48/48, finding all 24 required searches and avoiding all 24 prohibited searches. `gpt-5.4-mini` scored 47/48, finding 23/24 required searches and avoiding all 24 prohibited searches. All 96 trials were valid. Mini's one false negative was audited against the current rule and business context; no answer-key correction was warranted. Keep `gpt-5.5` as the operating agent. Mini remains validated for bounded query writing by the separate retrieval experiment. Report: `evals/reports/search_decision_model_comparison.md`.

Current decision: BM25 remains the lexical baseline/control. The active product path is one corpus-guided, unfiltered query through hybrid retrieval, cached embeddings, and a Pinecone-backed vector store behind a vector-store interface. The local in-memory vector backend stays as the fast dev/eval baseline. The earlier constrained-variant result remains useful evidence about backend capacity and Pinecone parity, but it no longer defines the runtime query policy.

Current source-event trace result: `evals/advisor_source_event_cases.jsonl` now tests the active one-query `SearchRequest` contract. Six isolated acting-agent runs saw the case context but not the expected labels. The scorer checks search/no-search restraint, one event per distinct evidence job, required query concepts, exact agreement between the authored and executed query, the original user turn, and inspected chunk IDs. All 6/6 cases pass, with 7/7 expected events matched and no extras. Two apparent failures were answer-key defects: one additional search supported a separately cited prioritization rule, and one valid teaching query was rejected for omitting an unnecessary literal phrase. The run artifacts were frozen before correcting those labels. Report: `evals/reports/advisor_source_event_traces.md`.

The anti-over-search restraint is intentionally framed as a general claim-support rule, not as a case-specific route. Known economics can appear in an answer without requiring a fresh `diagnostic_evidence` search; the agent should search diagnostics only when the answer needs source support for a diagnostic claim. The regression guards against overfitting this rule by retaining counter-cases where diagnostic search is required (`sourceevents_v1_001` and `sourceevents_v1_002`) alongside cases where it should be absent (`sourceevents_v1_003` and `sourceevents_v1_004`).

Product-smoke stage: the component evals now catch many important failure modes, but a valid trace is not the same thing as a useful advisor. `evals/advisor_product_smoke_scenarios.jsonl` defines three realistic multi-turn sessions that test the product as a user would experience it: incomplete context, numbers arriving gradually, recommendations under challenge, source-backed explanations, snapshot updates, calculations, source search, query variants, citations, and final advice. Acting-agent runs are recorded under `evals/runs/product_smoke/v1/` and summarized in `evals/reports/advisor_product_smoke_v1.md`.

The first product-smoke result is directionally encouraging but not a clean victory lap. The advisor handled context gathering, saved state, calculations, source-backed explanations, and user pushback better than the earlier component-level failures suggested. The main modeling lesson is restraint: 1584's "STR Design Diagnostic" is a business-specific proposed package, not a named Money Models framework. It may function as an `attraction_offer` / front-end offer, but the system should not grow a bespoke diagnostic-offer data structure from one business case. Secondary findings were a stale payback fixture, now corrected, and noisy recommendation retrieval for front-end/attraction-offer searches.

Review of the partial/miss cases suggests this is mostly an eval-design and taxonomy-precision problem, not a search-decision problem. For ad-spend capacity (`sourceneed_v1_003`), the correct intent remains diagnostic because the user is asking how to interpret known economics, not which fix to implement. For recurring maintenance (`sourceneed_v1_006`), the correct intent remains recommendation and the primary layer remains continuity; payback can be a focus term without adding the unit-economics layer when the source claim is about a fix. For payment plans (`sourceneed_v1_007`), downsells is the right layer because the business function is reducing immediate purchase friction. For free trials (`sourceneed_v1_008`), the layer should remain offers plus downsells, but the intent can reasonably be either teaching or recommendation. For front-end offers (`sourceneed_v1_010`), the low focus score is a metric false negative: terms like "front-end offer" and "engagement" are semantically aligned with "front end offer" and "get leads to engage" but fail exact substring matching.

Intent, corrected: `SourceNeed.intent` was meant to be the retrieval objective for one search call. In the v1 implementation it is not — retrieval is driven by `layers`, `focus_terms`, and `query_variants`, and `intent` is never passed to the search. So a scored `intent` was grading a field that changes no output, and the diagnostic-vs-recommendation label was a source of false failures (a model could pick a reasonable label that did not match the recorded one, on a distinction the system does not act on). Intent is therefore demoted to a recorded annotation: the agent still emits it for trace readability, but it does not gate strict case pass. The rule of one retrieval job per search still holds and is enforced through `layers` and the split guidance, because those do drive retrieval. If intent is ever made load-bearing, the honest place for it is answer construction — a teaching answer, a diagnostic answer, and a recommendation answer owe the reader different things — not retrieval, where it would only duplicate `layers`. Focus-term concept coverage should be judged by an agent and recorded with rationale, while exact substring recall remains only a deterministic debugging signal.

## Advisor Loop

The advisor should be agent-led in conversation, with deterministic code only where the justification is strong:

- arithmetic and formulas
- snapshot persistence
- schema/readiness checks
- local retrieval execution
- trace logging

The advisor can teach, compare, diagnose, calculate, recommend, clarify, or update saved context. That choice should come from conversational reasoning, not a brittle keyword router.

The CLI should expose operations the agent can use:

- `setup_state`: create/load `.money-model-advisor/business_snapshot.json`
- `session_start`: prepare one advisor turn with state summary, recent traces, available operations, and trace requirements
- `read_snapshot`: inspect saved business facts
- `update_snapshot`: persist accepted facts from the human or inspected docs
- `turn_record`: persist the completed agent turn
- `calculate`: deterministic formulas
- `diagnose`: deterministic unit-economics diagnosis helpers
- `search_source_material`: local Money Models corpus retrieval
- `logs`: inspect saved advisor session turns

The operating rules for using those commands live in `ADVISOR_OPERATING_GUIDE.md`. A project-local skill version lives at `.codex/skills/money-model-advisor/SKILL.md`. Humans may run the same CLI commands directly for development, debugging, and manual control.

## Current Decision

The next implementation work is not external model-service integration. The settled path is:

1. treat the current next-action classification eval as the local baseline for tool-use judgment;
2. repair the agent/CLI boundary so the agent plans and the CLI records/executes deterministic tools;
3. add explicit source-need search and turn recording; **implemented**
4. formalize the eval cases as a golden-dataset suite; **implemented in `GOLDEN_DATASET.md`**
5. implement agent-generated query variants as the next query-generation experiment; **implemented**
6. keep all active work auditable and cost-aware.

This keeps the project aligned with the actual product use case and avoids premature infrastructure.
