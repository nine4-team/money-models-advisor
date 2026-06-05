# Architecture

This is the active technical reference for the local, subscription-operated Money Model Advisor.

The v1 system is not a provider-key model agent. It is a CLI-first local tool surface that a Codex/ChatGPT subscription context can operate.

## Runtime Shape

```text
money-model-advisor setup --business-dir /company
→ create/update .money-model-advisor/business_snapshot.json

money-model-advisor chat --business-dir /company --message "..."
→ load saved BusinessSnapshot
→ update accepted facts when obvious
→ run deterministic calculations when fields are present
→ retrieve local Money Models source chunks when evidence is needed
→ persist session trace

money-model-advisor search "CAC payback period" --layer unit-economics
→ return citation-ready Money Models source chunks

money-model-advisor snapshot --business-dir /company
→ show saved BusinessSnapshot

money-model-advisor snapshot set --business-dir /company economics.cac=350
→ update accepted snapshot fields

money-model-advisor logs --business-dir /company
→ show saved advisor session turns
```

The advisor reasoning happens in the subscription context. The repo supplies durable state and local tools.

## Core Components

| Component | File |
|---|---|
| Business snapshot schema | `src/money_model_architect/snapshot.py` |
| Setup/intake state | `src/money_model_architect/setup_intake.py` |
| Business directory manifest | `src/money_model_architect/business_context.py` |
| Deterministic formulas | `src/money_model_architect/calculator.py` |
| Unit-economics diagnosis helpers | `src/money_model_architect/diagnose.py` |
| Corpus layers | `src/money_model_architect/namespaces.py` |
| Local chunking and BM25-style retrieval | `src/money_model_architect/retrieval.py` |
| Advisor retrieval evidence capture | `src/money_model_architect/advisor_retrieval.py` |
| Advisor query construction from snapshot state | `src/money_model_architect/advisor_queries.py` |
| First stateful advisor skeleton | `src/money_model_architect/advisor.py` |
| CLI commands | `src/money_model_architect/cli.py` |
| Advisor operating instructions | `ADVISOR_OPERATING_GUIDE.md`, `.codex/skills/money-model-advisor/SKILL.md` |

## State Contract

`BusinessSnapshot` is the cache for accepted business facts. It stores:

- business type, ICP, and delivery model
- current money-model stack
- CAC, first-30-day gross profit, recurring gross profit, gross margin, LTGP, and payback
- user goal, reported symptoms, and diagnosed constraints
- missing fields and advisory status
- field source metadata

Setup can inspect optional local files and ask for missing information. Runtime chat should use the saved snapshot. If the user provides a missing fact in chat, the advisor saves it to the snapshot.

## Retrieval Contract

Retrieval means local search over the Money Models source corpus. It returns cited chunks with IDs, chapters, layers, scores, and previews.

Retrieval does not mean:

- web search
- provider-key calls
- rereading local business files
- intent routing

The active retriever is a BM25-style local baseline over heading-aware transcript chunks. More complex retrieval is not active unless it can be evaluated locally and earns the added complexity.

## Corpus Layers

| Layer | Chapters |
|---|---|
| `unit-economics` | CAC, payback period, gross profit, CFA, money model context |
| `offers` | attraction offers, offer types, decoy offers, free giveaways, free trials, free-with-consumption |
| `upsells` | classic upsell, menu upsell, anchor upsell, rollover upsell, buy X get Y |
| `downsells` | downsells, feature downsells, pay less now, payment plans, waived fee, win your money back |
| `continuity` | continuity offers, continuity bonus, continuity discounts |

Some cross-cutting chapters are tagged across layers so they can surface when useful.

## Deterministic Boundaries

Deterministic code is appropriate for:

- formulas
- snapshot persistence
- schema/readiness checks
- local retrieval execution
- session trace writing

It is not appropriate as the production conversational brain. The advisor should not use regex or shallow keywords to decide whether the user wants teaching, diagnosis, comparison, or recommendation.

## Evaluation

Active local evals:

| Check | Command |
|---|---|
| Unit tests | `python3 -m unittest discover -s tests -v` |
| Smoke eval | `PYTHONPATH=src python3 scripts/eval_smoke.py` |
| Local retrieval baseline | `PYTHONPATH=src python3 scripts/eval_retrieval.py` |
| Chunking comparison | `PYTHONPATH=src python3 scripts/compare_chunking.py` |
| Query realism audit | `PYTHONPATH=src python3 scripts/audit_query_realism.py` |
| Required-claim support | `PYTHONPATH=src python3 scripts/score_obligation_support.py` |

Archived provider-backed experiments are not active architecture.

## JD Mapping

| JD idea | Active local artifact |
|---|---|
| Chunking strategy | `src/money_model_architect/retrieval.py`, `evals/reports/chunking_comparison.md` |
| Namespaces / corpus layering | `src/money_model_architect/namespaces.py` |
| Golden datasets | `evals/golden.jsonl`, `evals/realistic_queries.jsonl`, `evals/obligations.jsonl` |
| Retrieval metrics | `scripts/eval_retrieval.py` |
| Tool use / agentic workflow | CLI commands plus `BusinessSnapshot` state |
| Deterministic calculations | `src/money_model_architect/calculator.py` |
| Caching for token savings | `BusinessSnapshot` caches accepted business facts so chat does not reread business files every turn |
| Observability | `.money-model-advisor/sessions/` traces |

## Deliberately Out Of Scope For V1

- provider-key model integration
- external embedding calls
- provider-key management
- hosted vector databases
- web UI
- multi-agent orchestration
- production auth, billing, or multi-tenancy
