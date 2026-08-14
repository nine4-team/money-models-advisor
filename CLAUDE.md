# Claude Guidance

This repository is the CLI/core/evaluation artifact for the Money Models Advisor portfolio project.

Read `JOB_DESCRIPTION.md` first. The target is the Acquisition.com Senior AI Engineer role, so design and implementation choices should make the engineering judgment obvious: agent/tool boundaries, RAG evaluation, golden datasets, cached embeddings, traceability, cost awareness, and failure analysis.

## Repo Boundary

Keep this repo focused on:

- Python CLI/core behavior;
- local advisor state and deterministic tools;
- retrieval, embeddings, Pinecone/local vector-store boundaries;
- golden datasets, scorers, reports, and narrative;
- Codex/CLI-style agent-operation docs and skills.

Do not build hosted-agent/API/web-product code in this repo. Hosted work belongs in:

```text
/Users/benjaminmackenzie/Dev/money-models-advisor-hosted
https://github.com/nine4-team/money-models-advisor-hosted
```

If hosted work needs a shared core behavior change, make the core change here only when it belongs to the CLI/core abstraction, then document how the hosted repo should consume it.

## Current Mental Model

```text
human talks to an agent
-> agent follows advisor operating guidance
-> agent runs CLI commands
-> CLI persists state, calculates, searches, and records traces
-> agent writes the final answer
```

The agent owns semantic judgment: next action, whether source search is needed,
single-query content, chunk usefulness, accepted memory updates, and answer quality.

The CLI/core owns deterministic work: snapshot persistence, formulas, retrieval execution, embedding cache use, trace validation, report generation, and scorer execution.

## Key Files To Read

- `AGENTS.md`: repo-wide development instructions.
- `.codex/skills/money-model-advisor/SKILL.md`: how an agent should operate the CLI during a Money Models conversation.
- `DESIGN.md`: canonical current design and decision record.
- `GOLDEN_DATASET.md`: map of golden datasets, product risks, scorers, and current results.
- `README.md`: command map and project status.

## Cost Rule

Do not run paid provider/model/SDK evals from this repo by default. Embedding API calls are allowed only for deterministic vectorization experiments when needed, with cache behavior recorded.

## Working Rules

- Preserve the CLI/core as platform-agnostic.
- Do not reintroduce deterministic chat synthesis as the advisor brain.
- Do not hide model/API use inside unrecorded scripts.
- Do not commit `.env`, API keys, `.cache/embeddings/`, or local advisor state.
- Do not push hosted-agent WIP into this repo.
- If you change behavior, identify the product risk, update/add the smallest relevant golden case, run the scorer, and record the interpretation in the right doc.

## Verification

Prefer focused checks first:

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/eval_smoke.py
python3 scripts/eval_search_decision_models.py --limit 2
python3 scripts/eval_source_event_traces.py
git diff --check
```

Run retrieval/backend comparisons only when touching retrieval behavior.
