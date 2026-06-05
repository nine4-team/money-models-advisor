# Building a Money Model Advisor

This is the canonical narrative for the current project direction.

The product is a CLI-first advisor for Alex Hormozi's *$100M Money Models*. It helps a founder diagnose unit economics, understand the money-model stack, compare concepts, and choose the next practical change to test. The advisor is operated through Codex/ChatGPT subscription context over local CLI tools and saved local state. The active design does not use provider-key model calls.

## Corrected Product Frame

The advisor is not a one-shot retrieval bot. A realistic user starts with a conversational goal:

- "Help me build a money model."
- "I think CAC is too high."
- "Our offer works, but cash is tight."
- "What should I add after the first sale?"
- "Explain rollover upsells in my situation."

Those are different advisory moves. The system should maintain a structured `BusinessSnapshot`, ask for missing context when needed, run deterministic calculations where appropriate, retrieve source evidence from the Money Models corpus when citations are needed, and then answer.

The v1 runtime is:

```text
setup local business snapshot
→ chat through Codex/ChatGPT subscription context
→ use local CLI tools for snapshot, calculation, retrieval, and trace logging
→ answer with cited source chunks when evidence is needed
```

No provider-key model call is part of the active advisor runtime.

## Corpus And State

The source corpus is transcribed into `corpus/transcripts/`, one lesson per file. The corpus naturally separates into five layers:

| Layer | Purpose |
|---|---|
| `unit-economics` | CAC, gross profit, payback period, CFA, diagnostic math |
| `offers` | attraction offers and front-end offer types |
| `upsells` | post-sale monetization and premium options |
| `downsells` | save offers, payment plans, lower-friction alternatives |
| `continuity` | recurring offers, retention, discounts, continuity bonuses |

The key runtime object is `BusinessSnapshot`, defined in `BUSINESS_SNAPSHOT_V1.md`. It stores accepted business facts, source metadata, calculated economics, missing fields, and advisory status. It is the cache for business context. Chat should use the snapshot, not reread every local business file on every turn.

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
- making provider-key calls

The current local baseline uses BM25-style scoring and the five-layer taxonomy. It is intentionally simple because the advisor loop, state model, and evaluation method need to be clear before adding retrieval complexity.

Local baseline:

| Retriever | Hit@1 | Hit@5 | MRR |
|---|---:|---:|---:|
| BM25 heading-aware | 81.25% | 100.00% | 0.8917 |

Report: `evals/reports/local_retrieval_baseline.md`.

## Evaluation Philosophy

The project is still experiment-first, but all active experiments must run locally or through subscription-operated review. The point is to demonstrate clear engineering judgment, not to accumulate fragile experiments.

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

Archived provider-backed experiments live under `archive/provider-backed-experiments/` and are not part of the active design.

## Advisor Loop

The advisor should be LLM-led through the subscription context, with deterministic code only where the justification is strong:

- arithmetic and formulas
- snapshot persistence
- schema/readiness checks
- local retrieval execution
- trace logging

The advisor can teach, compare, diagnose, calculate, recommend, clarify, or update saved context. That choice should come from conversational reasoning, not a brittle keyword router.

The local tool surface should expose:

- `setup`: build/update `.money-model-advisor/business_snapshot.json`
- `chat`: run one stateful advisor turn from saved snapshot
- `calculate`: deterministic formulas
- `diagnose`: deterministic unit-economics diagnosis helpers
- `search`: local Money Models corpus retrieval
- `snapshot`: show the saved business snapshot
- `snapshot set`: update accepted snapshot fields from the CLI
- `logs`: inspect saved advisor session turns

The operating rules for using those tools live in `ADVISOR_OPERATING_GUIDE.md`. A project-local skill version lives at `.codex/skills/money-model-advisor/SKILL.md`.

## Current Decision

The next implementation work is not model-provider integration. It is making the subscription-operated CLI advisor easier to use:

1. add small behavior evals for clarify/calculate/teach/diagnose/retrieve/recommend turns;
2. expand visible answer synthesis beyond the first payback/recommendation path;
3. keep all active work local and auditable.

This keeps the project aligned with the actual product use case and avoids premature infrastructure.
