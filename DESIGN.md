# Building a Money Model Advisor

This is the canonical narrative for the current project direction.

The product is an agent-operated advisor for Alex Hormozi's *$100M Money Models*. It helps a founder diagnose unit economics, understand the money-model stack, compare concepts, and choose the next practical change to test. A human talks to an agent; the agent follows the project skill's guidance; the agent runs the local CLI against saved local state. The active design does not call external model services.

## Corrected Product Frame

The advisor is not a one-shot retrieval bot. A realistic user starts with a conversational goal:

- "Help me build a money model."
- "I think CAC is too high."
- "Our offer works, but cash is tight."
- "What should I add after the first sale?"
- "Explain rollover upsells in my situation."

Those are different advisory moves. The system should maintain a structured `BusinessSnapshot`. The agent inspects local business docs as needed, saves accepted facts to the snapshot, then runs `chat`. Advisory turns should go through `chat`, which persists the trace, uses the saved snapshot, runs deterministic calculations where appropriate, searches the Money Models corpus when source support is needed, and returns the answer for the agent to relay.

The v1 runtime is:

```text
human asks agent for advice
→ agent follows Money Model Advisor skill guidance
→ agent inspects local docs if snapshot context is missing
→ agent saves accepted facts to BusinessSnapshot
→ agent runs local CLI commands for calculation, source search, and trace logging
→ agent answers with cited source chunks when support is needed
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

The key runtime object is `BusinessSnapshot`, defined in `BUSINESS_SNAPSHOT_V1.md`. It stores accepted business facts, source metadata, calculated economics, missing fields, and advisory status. It is the cache for business context. The agent may inspect local docs before updating the snapshot. `chat` should use the snapshot, not crawl local business files.

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

For next-action classification, the project uses a trace recorder rather than a deterministic planner. The recorder prepares isolated eval directories, copies fixtures, hides expected labels from the acting agent, captures observable workflow evidence, and writes `run.json`. It does not choose the advisor's next action. That separation matters because the eval subject is the skill-guided agent's judgment, not a hard-coded runner.

The trace design separates three roles:

- the acting agent performs the case using the skill and local CLI
- the trace extractor maps commands, logs, file reads, session fields, and snapshot diffs into `actual_actions[]`
- the scorer compares `actual_actions[]` against the case labels

This prevents self-report from becoming the metric and keeps weak evidence visible as `inferred` or `missing`.

Current next-action result: all 24 cases have completed trace artifacts. Dev/regression traces were captured in-thread by Codex; scenario holdout traces were run after prompt freeze with separate acting agents that saw acting prompts but not expected labels. After adjudicating one overly strict first-action label, the current report shows 100.0% first-action accuracy, 1.000 required-action recall, 100.0% full-sequence pass rate, 0% false-search rate, 0% missed-search rate, and 100% trace completeness. The adjudicated holdout case originally required logs as the literal first action for prior-conversation recall, but senior review concluded that reading snapshot first was harmless context-loading because logs were still read before the answer. The case label records this adjudication explicitly.

Current source-query result: the first seed query-quality eval covers 10 search-appropriate turns. Reference mode, which uses reviewer-authored source-specific queries, reports 100.0% known-useful Hit@3/Hit@5. Generated mode now passes an explicit advisor-selected `SourceNeed` into the runtime query builder and also reports 100.0% known-useful Hit@3/Hit@5, with no duplicate query reuse. This fixes the earlier snapshot-only failure where generated mode scored 50.0% and repeated a broad diagnostic query. The known-useful chunk labels are non-exhaustive seed labels, so this is a query-development baseline, not a production IR benchmark. The remaining gate is whether the acting agent reliably selects the right source need before calling search.

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
- `read_snapshot`: inspect saved business facts
- `update_snapshot`: persist accepted facts from the human or inspected docs
- `chat`: run one stateful advisor turn from saved snapshot and persist the trace
- `calculate`: deterministic formulas
- `diagnose`: deterministic unit-economics diagnosis helpers
- `search_source_material`: local Money Models corpus retrieval
- `logs`: inspect saved advisor session turns

The operating rules for using those commands live in `ADVISOR_OPERATING_GUIDE.md`. A project-local skill version lives at `.codex/skills/money-model-advisor/SKILL.md`. Humans may run the same CLI commands directly for development, debugging, and manual control.

## Current Decision

The next implementation work is not external model-service integration. The settled path is:

1. treat the current next-action classification eval as the local baseline for tool-use judgment;
2. test whether the acting agent reliably selects the right source need before calling source-material search;
3. expand visible answer synthesis beyond the first payback/recommendation path;
4. keep all active work local and auditable.

This keeps the project aligned with the actual product use case and avoids premature infrastructure.
