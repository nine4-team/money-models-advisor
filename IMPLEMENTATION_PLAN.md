# Implementation Plan

This project should be built experiment-first.

The architecture docs describe the intended system. The implementation plan keeps the work honest: every major RAG or agent choice should either be part of the minimal runnable slice or justified by an evaluation report.

## Principle

Treat RAG architecture like ML model selection:

1. Define the candidate techniques.
2. Run them against the same evaluation set.
3. Compare quality, latency, cost, and failure modes.
4. Adopt the simplest variant that clears the decision rule.
5. Record the decision in `evals/reports/`.

The goal is not to build every sophisticated component immediately. The goal is to make each added component earn its place.

## Current product direction

The next real product slice is CLI-first with two modes:

```bash
money-model-advisor setup --business-dir /path/to/company
money-model-advisor chat --business-dir /path/to/company
```

`setup` builds the initial `BusinessSnapshot` from setup/intake and optional local files. `chat` uses the saved snapshot only. If the user provides missing information during chat, the advisor saves that fact back into the snapshot with source metadata. This keeps `BusinessSnapshot` as the cache and avoids rereading local files during every advisor turn.

The v1 snapshot contract is defined in `BUSINESS_SNAPSHOT_V1.md`.

Tooling recommendations are recorded in `TOOLING_SHORTLIST.md`.

**CLI setup and advisor loop:**

```mermaid
flowchart TD
  A["RUN SETUP<br/><small>money-model-advisor setup --business-dir /company</small>"] --> B["OPTIONAL LOCAL FILES<br/><small>notes, metrics, offers, funnel docs</small>"]
  A --> C["BUILD BUSINESS SNAPSHOT<br/><small>accepted facts + source metadata</small>"]
  B --> C

  C --> D["RUN CHAT<br/><small>money-model-advisor chat --business-dir /company</small>"]
  D --> E["USER MESSAGE<br/><small>current turn</small>"]
  C --> F["PLAN NEXT TURN<br/><small>use saved snapshot</small>"]
  E --> F

  F --> G{"ENOUGH CONTEXT?"}
  G -- "No" --> H["ASK CLARIFYING QUESTION<br/><small>only the next needed field</small>"]
  H --> E
  E --> S["SAVE NEW FACTS<br/><small>update BusinessSnapshot when user provides missing info</small>"]
  S --> C

  G -- "Yes" --> I{"TASK TYPE"}
  I -- "Calculate" --> J["DETERMINISTIC CALCULATOR<br/><small>unit-economics formulas</small>"]
  I -- "Diagnose / critique / design" --> K["DIAGNOSE CONSTRAINT<br/><small>from snapshot and calculations</small>"]
  I -- "Teach / compare" --> L["DIRECT RETRIEVAL<br/><small>framework explanation or comparison</small>"]

  J --> K
  K --> M["SELECT CORPUS LAYER<br/><small>namespace for current constraint</small>"]
  L --> M

  M --> N["RETRIEVAL STACK<br/><small>BM25 / dense / hybrid as appropriate</small>"]
  N --> O["RERANKER<br/><small>optional precision pass</small>"]
  O --> P["TOP CITED CHUNKS<br/><small>source excerpts for answer</small>"]

  P --> Q["ADVISOR ANSWER<br/><small>recommendation, citations, next action</small>"]
  J --> Q
  Q --> R["PERSIST SESSION TRACE<br/><small>snapshot, tool calls, chunks, answer</small>"]
  R --> E
```

## Current baseline

Implemented:

- Local transcript corpus search with BM25-style scoring.
- Five-layer namespace taxonomy with primary and secondary chapter roles.
- Deterministic unit-economics formulas.
- Constraint diagnosis aligned to the coach diagnostic flow.
- 32-query retrieval eval in `evals/golden.jsonl`.
- Local retrieval baseline report in `evals/reports/local_retrieval_baseline.md`.
- Chunking comparison report in `evals/reports/chunking_comparison.md`.
- API-backed retrieval ablation in `evals/reports/retrieval_ablation.md`.
- Reviewed required-claim support labels in `evals/obligations.jsonl`.
- Local required-claim review UI in `scripts/review_obligations.py`.
- Required-claim support scorer in `scripts/score_obligation_support.py`.
- Required-claim retrieval ablation in `evals/reports/retrieval_required_claim_ablation.md`.
- SQLite embedding cache in `.cache/embeddings.sqlite3`, implemented by `src/money_model_architect/embeddings.py`, so API-backed eval reruns do not re-embed unchanged corpus/query text.
- `BusinessSnapshot v1` schema and JSON persistence in `src/money_model_architect/snapshot.py`.
- Setup/intake state directory and manifest hashing in `src/money_model_architect/business_context.py`.
- Setup/intake answer collection in `src/money_model_architect/setup_intake.py`.
- Advisor query policy in `ADVISOR_QUERY_POLICY_V1.md` and `src/money_model_architect/advisor_queries.py`.
- First stateful advisor turn in `src/money_model_architect/advisor.py`.
- `setup` and `chat` CLI commands. `sync` remains an alias for `setup`.
- Framework-aware chunking candidate implemented, but not adopted as default.
- Unit test for the calculator.

Run checks:

```bash
PYTHONPATH=src python3 scripts/eval_smoke.py
PYTHONPATH=src python3 scripts/eval_retrieval.py
PYTHONPATH=src python3 scripts/compare_chunking.py
PYTHONPATH=src python3 scripts/retrieval_ablation.py
PYTHONPATH=src python3 scripts/retrieval_required_claim_ablation.py
PYTHONPATH=src python3 scripts/score_obligation_support.py --include-proposed
PYTHONPATH=src python3 -m money_model_architect.cli setup --business-dir /tmp/mma-demo-business
PYTHONPATH=src python3 -m money_model_architect.cli setup --business-dir /tmp/mma-demo-business --answers '{"business":{"business_type":"coaching business","icp":"gym owners"},"money_model":{"core_offer":{"description":"implementation program","price":5000},"attraction_offer":{"exists":true},"upsell":{"exists":false},"downsell":{"exists":true},"continuity":{"exists":false}},"economics":{"cac":350,"first_30_day_gross_profit":120},"problem":{"user_goal":"diagnose cash payback"}}'
PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir /tmp/mma-demo-business --message "We are a coaching business. Core offer is implementation program. CAC is $350 and first-30-day gross profit is $120. I want to diagnose cash payback."
python3 -m unittest discover -s tests -v
```

## Phase 1 — Evaluation Harness

Objective: make architecture comparisons easy to run.

Build:

- Expand `evals/golden.jsonl` from 5 records to roughly 30 records. **Done: 32 records.**
- Add retrieval metrics: hit@1, hit@5, MRR. **Done for local retrieval.**
- Write run outputs to `evals/runs/*.json`. **Done for local retrieval.**
- Add a report generator for Markdown tables. **Done for local retrieval.**

Acceptance criteria:

- A single command evaluates the current local retriever. **Done.**
- Results include per-query failures, aggregate metrics, and latency. **Done.**
- The first report can be generated without external services. **Done.**

First report:

- `evals/reports/local_retrieval_baseline.md`

## Phase 2 — Chunking Comparison

Objective: justify the chunking strategy with data.

Compare:

- Fixed-size windows. **Done for 300, 512, and 800 word variants.**
- Heading-aware transcript chunks. **Done.**
- Framework-aware chunks. **Done as a candidate.**
- Different target sizes and overlap settings. **Done for fixed-window baseline variants.**

Metrics:

- hit@5. **Done.**
- MRR. **Done.**
- average chunk tokens. **Done as average words per chunk.**

Decision rule:

Use the smallest chunking strategy that preserves framework completeness and does not regress retrieval quality beyond the configured threshold.

Current result:

- `heading-aware` wins the local BM25 comparison with Hit@1 81.25%, Hit@5 100%, and MRR 0.8917.
- Fixed windows all reached Hit@5 100%, but underperformed on Hit@1 and MRR.
- `framework-aware` slightly improves MRR to 0.8958, but does not clear the adoption rule because Hit@1 is unchanged and MRR gain is below 0.01.
- Required-claim support coverage is evaluated in Phase 3 as the support guardrail rather than during chunking selection.
- Adopted default remains `heading-aware`.

Report:

- `evals/reports/chunking_comparison.md`

## Phase 3 — Retrieval Ablation

Objective: prove whether hybrid retrieval is worth its cost and complexity.

Compare:

- BM25-only. **Done.**
- Dense-only. **Done with OpenAI `text-embedding-3-small`.**
- Dense + BM25 with reciprocal rank fusion. **Done as a candidate.**
- Dense + BM25 with score-sum fusion, if scores can be calibrated cleanly.

Metrics:

- hit@1. **Done.**
- hit@5. **Done.**
- MRR. **Done.**
- p50 / p95 retrieval latency. **Done.**
- exact-term recall for named frameworks
- required-claim support guardrail. **Done.**

Decision rule:

Adopt hybrid retrieval only if it improves named-framework and paraphrase retrieval enough to justify latency and implementation complexity.

Current result:

- `bm25`: Hit@1 81.25%, Hit@5 100%, MRR 0.8917.
- `dense-openai`: Hit@1 81.25%, Hit@5 100%, MRR 0.8958.
- `hybrid-rrf`: Hit@1 87.50%, Hit@5 100%, MRR 0.9375.
- `hybrid-rrf-lexical-anchor`: Hit@1 87.50%, Hit@5 100%, MRR 0.9375.
- Warm embedding-cache reruns report 0 API tokens and cache hits for unchanged embeddings, which keeps real API-backed experiments cheap enough to run repeatedly.
- Required-claim review status: 65 accepted labels, none needing attention.
- Accepted-label BM25 heading-aware required-claim support coverage: 87.69%, with 8 unsupported claims.
- Accepted-label retrieval ablation: `dense-openai` support coverage 90.77%, `hybrid-rrf` 89.23%, `bm25` 87.69%, and `hybrid-rrf-lexical-anchor` 87.69%.
- Decision: treat these as pilot results, not final retrieval-selection evidence. The harness can compare retrievers repeatably, but the pilot queries are too framework-vocabulary-heavy, chapter-level rank metrics are too coarse, and required-claim support labels are not exhaustive. The next methodology must start with realistic query design, then judge retrieved chunks directly before choosing among dense, hybrid, fusion, or rerank variants.

Report:

- `evals/reports/retrieval_ablation.md`
- `evals/reports/retrieval_required_claim_ablation.md`

## Phase 4 — Robust Retrieval Evaluation Methodology

Objective: define a chunk-level evaluation method that is strong enough to select among close retrieval approaches without overbuilding the label process.

Build:

- Replace the pilot query set with realistic user-intent queries.
- Draft set: `evals/realistic_queries.jsonl`.
- Methodology note: `evals/reports/query_realism.md`.
- Audit script: `scripts/audit_query_realism.py`.
- Include query types: exact framework names, paraphrases, business situations, diagnostic numeric scenarios, confusable near-neighbor questions, and noisy/vague user phrasing.
- Audit queries for lexical overlap with chapter titles and framework names so BM25 is not accidentally advantaged.
- For each eval query, collect top chunks from the candidate retrievers being compared.
- Pool builder: `scripts/build_chunk_relevance_pool.py`, outputting `evals/chunk_relevance_pool.jsonl`.
- Dedupe by chunk ID and avoid showing the reviewer which retriever proposed each chunk.
- Label each query/chunk pair as `0` not relevant, `1` partially useful, or `2` directly useful/supporting.
- Review UI: `scripts/review_chunk_relevance.py`.
- Scorer: `scripts/score_chunk_relevance.py`, outputting `evals/reports/pooled_relevance.md`.
- Keep required-claim labels as answer-readiness checks, not exhaustive relevance labels.

Metrics:

- nDCG@5 / nDCG@10
- precision@5
- recall@5 against the pooled judged set
- p95 latency and embedding cache usage

Decision rule:

Use pooled judgments when choosing between close retrieval or rerank variants. If pooled judgments agree with the cheaper existing metrics, keep the simpler metric for future smoke checks.

Reports:

- `evals/reports/query_realism.md`
- `evals/reports/pooled_relevance.md`

## Phase 5 — Embedding And Rerank Experiments

Objective: select model components by quality/cost frontier.

Compare embeddings:

- `text-embedding-3-large`
- `text-embedding-3-small`
- Cohere embed
- local BGE, if practical

Compare rerankers:

- No reranker.
- Cohere rerank.
- local BGE reranker, if practical

Metrics:

- nDCG@5 / nDCG@10 on pooled judgments
- precision@5
- required-claim support coverage
- p95 latency
- cost per query

Decision rule:

Use the cheapest model stack within the acceptable quality delta of the best-performing stack. Keep rerank only if it improves pooled relevance or required-claim support enough to justify latency and cost.

Reports:

- `evals/reports/embedding_comparison.md`
- `evals/reports/rerank_ablation.md`

## Phase 6 — CLI Stateful Advisor Slice

Objective: build the smallest useful advisor loop around real local business context.

Build:

- `money-model-advisor setup --business-dir <path>`. **Started as `setup`; supports `--interactive` and `--answers`; `sync` remains an alias.**
- `money-model-advisor chat --business-dir <path>`. **Started as `chat`; console-script alias added.**
- A business-context manifest that records files read, hashes, parse status, and extracted snippets. **Started: hashes, size, mtime, parse status.**
- A persisted `BusinessSnapshot` stored under `.money-model-advisor/` in the target directory. **Done.**
- Snapshot update from setup answers and the user's chat message. **Started for setup answers and obvious user-message facts.**
- A next-turn planner that chooses between clarify, calculate, diagnose, retrieve, critique, draft, compare, and teach. **Started for clarify/payback diagnosis; `advisory_status` tracks `insufficient_context`, `diagnosable`, `diagnosed`, and `recommendable`.**
- Targeted missing-field questions before diagnosis/design when the snapshot is incomplete. **Started.**
- Session trace output with tool calls, calculations, retrieved chunks, citations, and final answer. **Started: message, actions, snapshot, answer.**

Metrics:

- business-snapshot field extraction accuracy
- advisory-status accuracy
- next-action appropriateness
- deterministic calculation correctness
- citation coverage after retrieval
- user turns to useful recommendation

Decision rule:

Keep the CLI as the primary product surface until the advisor loop is useful without a web UI.

Report:

- `evals/reports/cli_stateful_advisor.md`

## Phase 7 — Advisor Tool Surface

Objective: verify that explicit stateful tools improve correctness and eval clarity.

Compare:

- Single retrieval endpoint.
- Stateless calculate + retrieve + diagnose tools.
- Stateful advisor tools: load context, update snapshot, plan next turn, calculate, diagnose, retrieve, critique, compare, draft.

Metrics:

- business-snapshot field extraction accuracy
- advisory-status accuracy
- next-action appropriateness
- deterministic calculation correctness
- constraint-identification accuracy
- structured-output validity
- citation coverage
- tool-loop failure rate

Decision rule:

Keep a separate tool only when it improves correctness, observability, or task-specific evaluation enough to justify the extra orchestration surface.

Report:

- `evals/reports/tool_surface.md`

## Phase 8 — Model Routing

Objective: demonstrate model-switching decisions based on data.

Compare:

- Default model for all tasks.
- Cheap model for snapshot extraction and conversation-mode planning.
- Cheap judge with escalation threshold sweep.

Metrics:

- extraction accuracy
- next-action accuracy
- answer quality
- cost per successful answer
- escalation precision

Decision rule:

Route to cheaper models when quality is statistically similar and cost improves materially. Escalate only where judge confidence predicts a quality gain.

Report:

- `evals/reports/routing_decisions.md`

## Non-goals for now

- Multi-tenant auth.
- Billing.
- Kubernetes or production infra.
- Fine-tuning.
- Multi-agent planner/executor systems.

Those can be revisited after the core evaluation story is real.
