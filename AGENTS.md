# Project Guidance For Codex

This repo is a portfolio project for the Acquisition.com Senior AI Engineer role. Read `JOB_DESCRIPTION.md` as the project north star before making design or implementation decisions.

## Core Objective

Build and document a Money Models advisor that demonstrates senior AI engineering judgment:

- production-oriented agent workflow design
- clear agent/tool boundaries
- RAG pipeline decisions with measured tradeoffs
- golden datasets and regression-oriented evaluation
- retrieval metrics, cached embeddings, and cost-aware design
- traceability, observability, and failure analysis

The goal is not to maximize feature count. The goal is to make the reasoning behind each architectural choice obvious and defensible for the target job description.

## Current Architecture

The product is agent-operated and CLI-backed:

```text
human talks to agent
-> agent follows project guidance and relevant skill instructions
-> agent runs local CLI tools for deterministic support
-> CLI persists state, calculates, searches, and records traces
-> agent composes the answer
```

The agent owns semantic judgment: next action, search-request generation, chunk usefulness, and final answer quality.

The CLI owns deterministic work: snapshot persistence, formulas, retrieval execution, embedding cache use, report generation, and trace recording.

Do not reintroduce deterministic chat synthesis as the advisor brain.

## Skills

Use `.codex/skills/money-model-advisor/SKILL.md` when operating the advisor for a human conversation. That skill is the runbook for using the CLI from a business context directory.

Keep repo-wide development guidance in this `AGENTS.md` file. Keep advisor-operation workflow details in the skill.

## Evaluation And Golden Dataset

Treat the eval cases as a golden-dataset suite, not ad hoc tests. `GOLDEN_DATASET.md` is the canonical map of datasets, product risks, scorers, reports, current results, and decisions. Design changes should be justified against the relevant golden data and reports.

Important eval assets include:

- `evals/advisor_tool_use_cases.jsonl`
- `evals/advisor_source_need_cases.jsonl`
- `evals/advisor_source_event_cases.jsonl`
- `evals/advisor_search_query_cases.jsonl`
- `evals/obligations.jsonl`
- `evals/reports/`

When adding or changing behavior:

1. Identify which product risk the change addresses.
2. Update or add golden cases if needed.
3. Run the relevant scorer.
4. Record results and interpretation in the appropriate narrative/progress doc.

Do not tune only for one visible miss unless the fix is framed as a general behavior and checked against non-miss cases.

## Retrieval Position

BM25 is the lexical baseline/control for citation-oriented source lookup, not the intended product architecture. The current product path is one corpus-guided, unfiltered query through hybrid retrieval over framework-aware chunks, with cached embeddings and a Pinecone-backed vector store behind a retrieval storage boundary. Across 46 audited regression cases, the corpus-guided method leads the raw-question and unguided controls under both tested query writers. With each saved query held fixed, hybrid ranks useful evidence earlier than BM25 under both `gpt-5.5` and `gpt-5.4-mini` and preserves 100% Hit@5; Useful@5 is mixed, so do not claim hybrid always produces a cleaner context. The relevance labels were audited by Codex rather than an independent human reviewer, so keep that limitation explicit. The local backend remains the fast eval baseline, and the older multi-query/filtering path remains only for historical reproducibility and separate future experiments.

Embedding API use is allowed for deterministic vectorization and cached retrieval experiments. Do not use external model APIs for agent planning, labeling, answer synthesis, or acting-agent eval work. Product model-routing evidence for agent behavior should use the Codex/CLI harness in `scripts/eval_codex_model_routing.py`. A separate explicit model/provider comparison experiment (such as `scripts/eval_model_routing.py`) may replay golden cases against external chat models only if every prompt and raw response is recorded and the report is clearly labeled as API replay, not the product harness.

Never commit `.env`, API keys, or `.cache/embeddings/`.

## Next High-Signal Work

The next JD-aligned work should emphasize:

- continued model-routing and tiering evals over the existing golden suites using the Codex/CLI harness, with quality, latency, token-proxy, and failure-mode comparison
- multi-provider comparison evidence where available, especially prompt behavior and trace reliability
- hosted-vector latency optimization now that Pinecone indexing and parity evals work
- continued golden-dataset breadth and regression coverage
- cold-cache reporting only if first-run embedding cost needs to be separated from steady-state warm-cache behavior

## Verification

Prefer running focused checks first, then the broader suite before commit:

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/eval_smoke.py
python3 scripts/eval_source_need_generation.py
python3 scripts/eval_source_event_traces.py
python3 scripts/compare_retrieval_backends.py --query-source generated --report evals/reports/retrieval_backend_comparison.md
git diff --check
```

Use additional eval commands when touching the relevant behavior.
