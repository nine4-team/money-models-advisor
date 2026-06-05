---
name: money-model-advisor
description: Operate the Money Model Advisor CLI using advisor state saved in the invocation folder. Use when advising on Money Models, updating saved BusinessSnapshot facts, searching local Money Models source material, inspecting advisor logs, or producing cited recommendations without provider-key model calls.
---

# Money Model Advisor

Use this skill to operate the Money Model Advisor CLI with advisor state read from and written to the folder where the skill is invoked.

## Core Rule

Reason conversationally first. Do not route by shallow keywords. Use tools only when they help clarify, calculate, retrieve source material, update state, or inspect prior turns.

Do not use provider-key model calls.

## Path Resolution

The user should not have to understand path plumbing. Resolve paths this way:

- `advisor_repo`: `/Users/benjaminmackenzie/Dev/money-model-architect`
- `context_dir`: the current working directory when the skill is invoked; this is where advisor state is read and written

Run CLI commands from `advisor_repo` and pass `context_dir` to the CLI's `--business-dir` flag.

## Operating Flow

1. Resolve `context_dir`.
2. Initialize or refresh local advisor state:

   ```bash
   cd /Users/benjaminmackenzie/Dev/money-model-architect
   PYTHONPATH=src python3 -m money_model_architect.cli setup --business-dir "$CONTEXT_DIR"
   ```

3. Inspect the saved snapshot:

   ```bash
   cd /Users/benjaminmackenzie/Dev/money-model-architect
   PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir "$CONTEXT_DIR"
   ```

4. If important context is missing, ask the next useful question in plain English. Do not ask the user to paste JSON.
5. Save clear user-provided facts with `snapshot set`.
6. If enough context exists, run an advisor turn with the user's actual request:

   ```bash
   cd /Users/benjaminmackenzie/Dev/money-model-architect
   PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir "$CONTEXT_DIR" --message "the user's request"
   ```

7. Return the advisor answer in plain English. Mention saved state or logs only when useful.

## Commands

Show saved state:

```bash
cd /Users/benjaminmackenzie/Dev/money-model-architect
PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir "$CONTEXT_DIR"
```

Update accepted facts:

```bash
cd /Users/benjaminmackenzie/Dev/money-model-architect
PYTHONPATH=src python3 -m money_model_architect.cli snapshot set --business-dir "$CONTEXT_DIR" economics.cac=350
```

Run deterministic math:

```bash
cd /Users/benjaminmackenzie/Dev/money-model-architect
PYTHONPATH=src python3 -m money_model_architect.cli calculate payback --inputs '{"cac":350,"month_one_gp":120,"monthly_recurring_gp":40}'
```

Search local source material:

```bash
cd /Users/benjaminmackenzie/Dev/money-model-architect
PYTHONPATH=src python3 -m money_model_architect.cli search "CAC payback period" --layer unit-economics --top-k 5
```

Inspect saved turns:

```bash
cd /Users/benjaminmackenzie/Dev/money-model-architect
PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir "$CONTEXT_DIR"
```

## Workflow

1. Load `snapshot` before business-specific advice.
2. Ask for missing context when the snapshot is insufficient.
3. Save clear user-provided facts with `snapshot set`.
4. Use `calculate` for payback, CAC, gross profit, gross margin, LTGP, and CFA level.
5. Use `search` when teaching, comparing, diagnosing, or recommending needs source support.
6. Cite inspected chunks inline, such as `[payback-period:0]`.
7. Use `logs` to inspect prior session turns.

## Guardrails

- Do not save guesses as snapshot facts.
- Do not reread local business files during chat; use `BusinessSnapshot`.
- Do not cite chunks you did not inspect.
- Do not turn every user message into retrieval.
- Prefer one clear clarifying question over premature recommendation.
