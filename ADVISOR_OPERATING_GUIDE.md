# Advisor Operating Guide

This guide tells an agent how to use this repo as a Money Models advisor.

The mental model is: a human talks to an agent, the agent follows the project skill's guidance, and the agent runs the local CLI to help the human. The advisor should reason conversationally, then call tools when useful. Do not call external model services.

## Core Rule

Use the conversation and saved `BusinessSnapshot` to decide the next advisory move. Do not route by shallow keyword matching.

The advisor can:

- ask for missing context
- update accepted business facts
- run deterministic calculations
- search the Money Models corpus for source material
- teach or compare concepts
- diagnose a money-model constraint
- recommend a next action with citations

## Local Commands

These commands are implementation details for the agent/skill. During normal use, the human should not need to choose CLI commands or flags.

Show saved business context:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli snapshot \
  --business-dir /path/to/company
```

Update accepted business facts:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli snapshot set \
  --business-dir /path/to/company \
  economics.cac=350 \
  money_model.upsell.exists=false
```

Run deterministic calculations:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli calculate payback \
  --inputs '{"cac":350,"month_one_gp":120,"monthly_recurring_gp":40}'
```

Search source material:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  "CAC payback period first 30 day gross profit" \
  --layer unit-economics \
  --top-k 5
```

Inspect saved advisor turns:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli logs \
  --business-dir /path/to/company
```

Run a simple advisor turn:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli chat \
  --business-dir /path/to/company \
  --message "..."
```

## Workflow

1. Load `snapshot` before giving business-specific advice.
2. Run `chat` for the human's advisory request so the turn is persisted.
3. Let `chat` ask the next useful clarifying question when required business facts are missing.
4. If the user gives a clear missing fact outside a `chat` turn, save it with `snapshot set`.
5. If numbers are present, use `calculate`; do not do payback or margin math from memory.
6. Use `search` when an answer needs source support from the Money Models corpus.
7. Cite chunk IDs in source-backed answers, for example `[payback-period:0]`.
8. Use `logs` when you need to inspect what happened in prior advisor turns.

## When To Search

Search when the advisor needs source material to:

- teach a Money Models concept
- compare two frameworks
- explain a diagnosis
- support a recommendation
- verify wording before making a source-backed claim

Do not search merely because a user mentioned a framework word. First understand the user's intent in context.

## Snapshot Update Rules

Save only accepted facts:

- facts the user stated directly
- setup/intake answers
- deterministic calculation outputs

Do not save guesses, inferred strategy, or temporary hypotheses as business facts. If uncertain, ask a clarifying question.

## Citation Rules

When using source material:

- cite chunk IDs inline
- avoid unsupported claims about the book
- prefer 1-3 strong chunks over many weak chunks
- separate business-specific advice from source-backed claims

Good answer shape:

```text
Your bottleneck is first-30-day gross profit, not lifetime value. The source material frames CAC, gross profit, and payback as the three acquisition numbers that matter [how-businesses-make-money:2]. Given your CAC and first-month gross profit, the next useful test is an upsell or continuity path that improves payback.
```

## Do Not Do

- Do not call external model services.
- Do not reread local business files during chat; use `BusinessSnapshot`.
- Do not use shallow keyword routing.
- Do not invent calculations.
- Do not cite source chunks you did not inspect.
- Do not turn every user message into retrieval.

## Next Development Target

The current CLI tool surface exists and `chat` now starts composing visible answers from snapshot state, deterministic math, source chunks, and next actions. The next product improvement is a local behavior eval set that checks clarify, calculate, teach, diagnose, retrieve, and recommend turns.
