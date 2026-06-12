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

The adopted local chunking strategy is `heading-aware`. It preserves transcript sections when possible and falls back to fixed windows when needed.

Measured local result:

| Strategy | Hit@1 | Hit@5 | MRR |
|---|---:|---:|---:|
| `heading-aware` | 81.25% | 100.00% | 0.8917 |
| `framework-aware` | 81.25% | 100.00% | 0.8958 |

Decision: keep `heading-aware`. The framework-aware candidate does not clear the adoption threshold because Hit@1 is unchanged and the MRR gain is too small.

Report: `evals/reports/chunking_comparison.md`.

## Retrieval Position

The active retrieval path is local corpus search over transcript chunks. Retrieval means: search the Money Models source corpus for chunks that can support the advisor's answer with citations.

It does not mean:

- searching the web
- rereading local business files
- deciding the user's intent
- calling external model services

The current local baseline uses BM25-style scoring and the five-layer taxonomy. It is intentionally simple because the advisor loop, state model, and evaluation method need to be clear before adding retrieval complexity.

The next retrieval work is not just "write better queries." The advisor must pass two gates:

1. Tool-use judgment: decide whether the current turn needs source-material search at all, versus snapshot/log lookup, local business-doc inspection, calculation, clarification, or direct answer synthesis.
2. Search-query quality: when source-material search is the right tool, build a source-specific query that retrieves useful Money Models chunks.

Query quality should be evaluated only on turns where source-material search is actually the right action.

This order matters. First we need to prove the agent can decide when to search and generate source-specific search requests. Then retrieval-model comparisons become meaningful. If the agent searches on the wrong turns or sends generic/stale queries, BM25, dense, hybrid, or reranking comparisons mostly measure noise from bad tool use rather than retrieval architecture quality.

Local baseline:

| Retriever | Hit@1 | Hit@5 | MRR |
|---|---:|---:|---:|
| BM25 heading-aware | 81.25% | 100.00% | 0.8917 |

Report: `evals/reports/local_retrieval_baseline.md`.

## Evaluation Philosophy

The project is still experiment-first, but all active experiments must run locally or through agent-assisted human review. The point is to demonstrate clear engineering judgment, not to accumulate fragile experiments.

Because the target JD explicitly calls for golden datasets, the eval assets are presented as a golden-dataset suite rather than a loose pile of scripts. `GOLDEN_DATASET.md` maps the case files, scorers, reports, current results, and decisions. The current suite covers several product risks: tool-use judgment, source-need generation, source-event logging, search-query quality, chunking, retrieval backend comparison, required-claim support, and product-level multi-turn advisor behavior.

Core design principle: the agent judges meaning; the CLI handles deterministic bookkeeping. The advisor is built around an agent that can read conversation context, inspect local docs, decide which tool is appropriate, generate source needs, and adjudicate semantic quality. The CLI should not pretend to be that semantic judge. Its job is to persist state, run formulas, execute local search, capture traces, and score recorded judgments. The detailed CLI product contract is defined in `CLI_DESIGN.md`.

This means deterministic code is appropriate for:

- snapshot schema, persistence, and source metadata
- unit-economics calculations
- numeric/accounting state classification after the agent has chosen the task
- local corpus search execution
- exact trace capture and report generation
- validation that recorded eval artifacts have the expected shape

Agent judgment is appropriate for:

- deciding the next advisory action
- generating `SourceNeed` objects
- judging whether retrieved chunks actually support a claim
- judging whether focus terms are conceptually covered even when wording differs
- adjudicating ambiguous intent/layer cases
- evaluating final answer quality, grounding, and usefulness

The system should record those agent judgments as auditable artifacts, with rationale, instead of burying semantic decisions in brittle keyword rules.

Senior audit refinement: deterministic code can classify numeric/accounting states such as "CAC is not recovered by first-30-day gross profit." That is not the same as deciding the user's conversational intent. Readiness flags, likely retrieval layers, and query terms are candidate hints; the agent decides whether they apply to the current turn.

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
| `evals/advisor_search_query_cases.jsonl` | search-appropriate turns for source-query quality |
| `scripts/eval_search_query_quality.py` | source-query quality scorer and report generator |
| `scripts/compare_retrieval_backends.py` | BM25/vector/hybrid comparison after source-need generation passes its seed gate |

For next-action classification, the project uses a trace recorder rather than a deterministic planner. The recorder prepares isolated eval directories, copies fixtures, hides expected labels from the acting agent, captures observable workflow evidence, and writes `run.json`. It does not choose the advisor's next action. That separation matters because the eval subject is the skill-guided agent's judgment, not a hard-coded runner.

The trace design separates three roles:

- the acting agent performs the case using the skill and local CLI
- the trace extractor maps commands, logs, file reads, session fields, and snapshot diffs into `actual_actions[]`
- the scorer compares `actual_actions[]` against the case labels

This prevents self-report from becoming the metric and keeps weak evidence visible as `inferred` or `missing`.

Current next-action result: all 24 cases have completed trace artifacts. Dev/regression traces were captured in-thread by Codex; scenario holdout traces were run after prompt freeze with separate acting agents that saw acting prompts but not expected labels. After adjudicating one overly strict first-action label, the current report shows 100.0% first-action accuracy, 1.000 required-action recall, 100.0% full-sequence pass rate, 0% false-search rate, 0% missed-search rate, and 100% trace completeness. The adjudicated holdout case originally required logs as the literal first action for prior-conversation recall, but senior review concluded that reading snapshot first was harmless context-loading because logs were still read before the answer. The case label records this adjudication explicitly.

Current source-query result: the golden search-query slice now covers 30 search-appropriate turns. Reference mode uses reviewer-authored source-specific queries. Generated mode passes an explicit advisor-selected `SourceNeed` into the runtime query builder. Generated-variants mode adds constrained agent-style query variants and keeps the deterministic `SourceNeed` query as a fallback. This fixes the earlier snapshot-only failure where generated mode scored 50.0% and repeated a broad diagnostic query. The known-useful chunk labels are non-exhaustive seed labels, so retrieved but unlabeled chunks are inspected and adjudicated before interpreting misses.

Current source-need result: `evals/advisor_source_need_cases.jsonl` defines 14 seed cases, including 10 source-search cases and 4 no-search controls. Blind acting-agent traces are captured under `evals/runs/source_need/taxonomy_v2/` and scored in `evals/reports/advisor_source_need_generation.md`. After taxonomy guidance and focus-alias cleanup, the current report shows 100.0% search decision accuracy, 0.0% false search rate, 0.0% missed search rate, and 100.0% correct no-search controls. Intent match is 100.0%, layer exact match is 90.0%, average layer recall is 0.950, and average focus-term concept recall is 0.750. Decision: source-need generation is now good enough for seed retrieval-backend comparisons, with one known residual: the free-trial case still chooses `offers` without also adding `downsells`.

Current retrieval-backend decision: after source-need generation met the seed gate, retrieval comparison became meaningful enough to run as an engineering experiment. The system now supports three backends over the same heading-aware chunks: BM25, vector, and hybrid. Vector search uses OpenAI embeddings only for deterministic vectorization, not for agent judgment or answer synthesis. Embeddings are cached under `.cache/embeddings/` so corpus vectors and repeated query vectors are reused across runs. Hybrid search uses reciprocal-rank fusion over BM25 and vector rankings so raw lexical and embedding scores do not need to be directly comparable.

Baseline retrieval-backend result: `evals/reports/retrieval_backend_comparison.md` compares the three backends on the 30 generated-query cases. BM25 is the lexical baseline/control, not the intended production architecture. It reaches 93.3% Hit@3, 100.0% Hit@5, and mean known-useful rank 1.43. Plain vector reaches 96.7% Hit@3/Hit@5 and misses `searchq_v1_001`; plain hybrid also reaches 96.7% Hit@3/Hit@5 and misses `searchq_v1_001`, with a better mean known-useful rank of 1.21. The likely lesson is that deterministic generated queries still contain exact framework terms, so lexical retrieval is unusually strong for citation-oriented source lookup; dense/hybrid retrieval can return semantically adjacent chunks while missing the clearest framework passage when the query is a flat noun list.

Miss adjudication matters because the labels are intentionally non-exhaustive. In the 30-case expansion, several apparent misses were actually label-set limitations: retrieved menu-upsell, rollover-upsell, waived-fee, and continuity-bonus chunks were directly citeable and were added to the known-useful labels after inspection. `searchq_v1_001` remains the true plain vector/hybrid top-5 weakness: the user asks why fulfillment cost matters for ads, and dense retrieval ranks adjacent payback/CAC/CFA chunks above the clearest gross-profit/fulfillment-cost explanation.

Senior review of the remaining miss concluded that deterministic query flattening was a reasonable v1 baseline because it separated risks: the agent selected the semantic `SourceNeed`, while the CLI produced a stable query that could be evaluated. The v2 direction should not be one unconstrained freeform agent query. It should be agent-generated query variants under a constrained schema, with the deterministic flattened query retained as a fallback variant. That preserves traceability while letting the agent express causal teaching queries such as "why cost to deliver affects gross profit and paid acquisition."

Query variants are now implemented as `SourceNeed.query_variants` plus a separate candidate file, `evals/advisor_query_variants_v2.jsonl`. The evaluator fuses variant results with reciprocal-rank fusion so repeated evidence across variants is promoted and early variants cannot simply crowd out the fallback. On the 30-case expanded set, generated variants produce 100.0% Hit@5 for BM25, vector, and hybrid. Hybrid is strongest: 100.0% Hit@3, 100.0% Hit@5, mean known-useful rank 1.17, and no top-5 misses. BM25+variants reaches 96.7% Hit@3 and 100.0% Hit@5; vector+variants reaches 96.7% Hit@3 and 100.0% Hit@5. The operational report makes the cost visible: generated variants use 4.0 queries per case and 120 vector searches across the 30-case slice. In the current warm-cache run, query and corpus embedding cache hit rates are 100.0%, so vector/hybrid made zero external embedding API batches.

Hiring narrative and product direction: BM25 is the lexical baseline/control, not the product architecture. It tells us whether fancier retrieval is actually earning its complexity. The target architecture is: agent generates structured `SourceNeed`; agent or planner generates constrained query variants; retrieval runs hybrid search over lexical + vector candidates; results are fused/reranked; embeddings are cached for cost control; golden datasets track quality regressions, latency, and cost.

The Pinecone/web-hosting narrative should say: "I started with local retrieval so I could iterate quickly and build reliable evals. Once the retrieval strategy was justified, I added a Pinecone-backed vector store behind the same interface, so the system could move from local CLI experimentation to hosted production retrieval without rewriting advisor logic."

Pinecone implementation note: the important architecture choice is the vector-store boundary, not whether the first Pinecone adapter uses the official SDK or direct HTTP calls. For this prototype, a small REST adapter keeps the rest of the advisor dependency-light and provider-agnostic: local evals, Pinecone evals, and a future hosted surface all call the same narrow `VectorStore` contract. In production, the internals of `PineconeVectorStore` could move to the official SDK if it improved retry handling, auth ergonomics, batching, observability, or long-term maintenance without changing advisor logic or eval code.

The write-up should frame the result this way: "I started with BM25 as a baseline because exact framework terms are strong in this corpus. Then I tested vector and hybrid retrieval. Plain vector/hybrid underperformed on one diagnostic case, which exposed a query-generation weakness. I added constrained query variants plus fusion, expanded the golden search-query slice from 10 to 30 cases, adjudicated newly retrieved citeable chunks, and found that hybrid+variants was strongest on the expanded slice. Because the dataset is still portfolio-scale, I would not overclaim final production superiority, but the production-facing architecture is hybrid retrieval with cached embeddings and eval-gated query generation."

Pinecone parity result: the corpus was indexed into Pinecone as 202 heading-aware chunk vectors using stable ids and citation metadata. The same 30-case generated-variants golden slice was then run against `--vector-store pinecone`. Quality matched the local direction: hybrid+variants reached 100.0% Hit@3, 100.0% Hit@5, mean known-useful rank 1.17, and no top-5 misses. Embedding cache behavior was also healthy: query cache hit rate was 100.0%, corpus vectors were already cached before indexing, and the eval made zero external embedding API batches.

The Pinecone run exposed a deployment tradeoff rather than a quality regression. The original hosted eval executed query variants sequentially, producing 120 Pinecone vector searches across 30 cases and p50 retrieval above 5s. After adding bounded per-case parallel retrieval (`--max-workers 8`), the same full 30-case Pinecone single-namespace benchmark completes successfully: hybrid+variants reaches 100.0% Hit@3, 100.0% Hit@5, mean known-useful rank 1.17, p50 retrieval about 1.43s, p95 about 1.76s, 120 vector searches, 100.0% query embedding cache hits, and zero embedding API batches. This should not be hidden in the write-up. The correct interpretation is: Pinecone proves the hosted vector-storage path and preserves retrieval quality, while production optimization should continue to bound query fanout, tune top-k, parallelize safely, and add request-level observability before claiming final latency readiness.

Pinecone namespace result: after correcting the design so the agent, not deterministic CLI routing, selects namespaces, the corpus was indexed into five Money Models layer namespaces: `money-models-unit-economics` (53 records), `money-models-offers` (87), `money-models-upsells` (68), `money-models-downsells` (57), and `money-models-continuity` (74). Local full-set oracle testing compared the single/default namespace condition against explicit `target_namespaces` populated from expected layers. Quality was unchanged: both conditions preserved hybrid+variants at 100.0% Hit@3/Hit@5 with mean known-useful rank 1.17. The namespace condition increased vector search count from 120 to 140 because multi-layer cases query multiple namespaces. The full 30-case Pinecone namespace benchmark now also completes under bounded parallelism. It preserves hybrid quality at 100.0% Hit@3/Hit@5 and mean rank 1.17, but p95 retrieval is worse than the single-namespace Pinecone run: about 3.01s versus 1.76s, with 140 vector searches instead of 120.

Per-case comparison strengthens this beyond the summary metrics: across all 90 (case, retriever) rows, the two conditions returned identical top-5 chunk ids in identical order. The namespace split did not change what was retrieved at all, even with oracle routing from expected layers — which is the best case any production router could reach. Namespaces would only help if wrong-layer chunks were crowding out right-layer ones, and on this corpus they are not.

The latency mechanism matters for the write-up: querying a smaller namespace is not faster, because at this corpus size (202 chunks) Pinecone query time is dominated by the network round-trip and fixed per-request overhead, not vector scan time. The split instead turns one round-trip into up to five for multi-layer cases, and the case completes only when the slowest namespace query returns. Taking the max of several draws from the same latency distribution worsens the tail — which is why p50 barely moved (about 1.43s vs 1.45s) while p95 went from 1.76s to 3.01s.

One caveat on scope: this eval slice is saturated. Hit@5 is 100% for every backend in every condition, and BM25 alone reaches 96.7% Hit@3, so the slice has no headroom to detect a quality improvement from anything. The supported claim is "no measurable difference on this slice," not "namespaces never help." If the corpus grows to the point where layers genuinely interfere in ranking, re-test with a harder slice before revisiting this decision.

Decision: five-layer namespaces are implemented and verified, but they are not a better v1 default than single namespace plus metadata filtering on this evaluation slice. The senior product choice is to keep namespace support, score agent namespace selection separately, and use the simpler single-namespace path by default until namespace routing shows a measured quality or latency win.

Decision: BM25 remains the lexical baseline/control. The target product path is hybrid retrieval with constrained query variants, cached embeddings, eval-gated promotion, and a Pinecone-backed vector store behind a vector-store interface. The local in-memory vector backend stays as the fast dev/eval baseline. The 30-case expanded slice plus Pinecone parity supports moving hybrid+variants to candidate default for the portfolio architecture, while requiring continued golden-set expansion and latency optimization before calling it production-final.

Current source-event trace result: `evals/advisor_source_event_cases.jsonl` defines the post-hardening source-event regression requested after senior review. The first case, `sourceevents_v1_001`, checks the 1584 "what should we fix first?" turn and expects two recorded source events: diagnostic unit-economics evidence plus recommendation evidence for the selected fix layer. Blind acting-agent traces exposed the intended failure mode twice: v1 used one broad recommendation/unit-economics event, and v2 used only one diagnostic event. After tightening the source-event guidance, v3 matched both expected source events. The regression has since expanded to six blind acting-agent cases covering multi-search, pure diagnosis, pure recommendation, missing-context no-search, teaching-only, and continuity recommendation turns. A follow-up cleanup reran the upsell recommendation case after adding restraint guidance against re-sourcing already-known diagnostics. The current report shows 100.0% case pass rate, 6 / 6 expected source events matched, and 0 extra source-event warnings.

The anti-over-search restraint is intentionally framed as a general claim-support rule, not as a case-specific route. Known economics can appear in an answer without requiring a fresh `diagnostic_evidence` search; the agent should search diagnostics only when the answer needs source support for a diagnostic claim. The regression guards against overfitting this rule by retaining counter-cases where diagnostic search is required (`sourceevents_v1_001` and `sourceevents_v1_002`) alongside cases where it should be absent (`sourceevents_v1_003` and `sourceevents_v1_004`).

Product-smoke stage: the component evals now catch many important failure modes, but a valid trace is not the same thing as a useful advisor. `evals/advisor_product_smoke_scenarios.jsonl` defines three realistic multi-turn sessions that test the product as a user would experience it: incomplete context, numbers arriving gradually, recommendations under challenge, source-backed explanations, snapshot updates, calculations, source search, query variants, citations, and final advice. Acting-agent runs are recorded under `evals/runs/product_smoke/v1/` and summarized in `evals/reports/advisor_product_smoke_v1.md`.

The first product-smoke result is directionally encouraging but not a clean victory lap. The advisor handled context gathering, saved state, calculations, source-backed explanations, and user pushback better than the earlier component-level failures suggested. The main modeling lesson is restraint: 1584's "STR Design Diagnostic" is a business-specific proposed package, not a named Money Models framework. It may function as an `attraction_offer` / front-end offer, but the system should not grow a bespoke diagnostic-offer data structure from one business case. Secondary findings were a stale payback fixture, now corrected, and noisy recommendation retrieval for front-end/attraction-offer searches.

Review of the partial/miss cases suggests this is mostly an eval-design and taxonomy-precision problem, not a search-decision problem. For ad-spend capacity (`sourceneed_v1_003`), the correct intent remains diagnostic because the user is asking how to interpret known economics, not which fix to implement. For recurring maintenance (`sourceneed_v1_006`), the correct intent remains recommendation and the primary layer remains continuity; payback can be a focus term without adding the unit-economics layer when the source claim is about a fix. For payment plans (`sourceneed_v1_007`), downsells is the right layer because the business function is reducing immediate purchase friction. For free trials (`sourceneed_v1_008`), the layer should remain offers plus downsells, but the intent can reasonably be either teaching or recommendation. For front-end offers (`sourceneed_v1_010`), the low focus score is a metric false negative: terms like "front-end offer" and "engagement" are semantically aligned with "front end offer" and "get leads to engage" but fail exact substring matching.

Next design decision: treat `SourceNeed.intent` as the retrieval objective for one search call, not as a complete label for the user's whole turn. A turn can be mixed: for example, the final answer may both teach and recommend. But a single source-material search should know which job it is doing, because teaching, diagnosis, comparison, and recommendation ask the corpus for different kinds of support. If an answer genuinely needs two different retrieval jobs, the planner should issue two source needs rather than one ambiguous mixed-intent source need. Eval labels can still declare `acceptable_intents` for cases where more than one primary retrieval objective is defensible; that is label-tolerance, not a different runtime contract. Focus-term concept coverage should be judged by an agent and recorded with rationale, while exact substring recall remains only a deterministic debugging signal.

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
