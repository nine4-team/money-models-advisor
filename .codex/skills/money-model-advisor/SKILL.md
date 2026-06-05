---
name: money-model-advisor
description: Operate the local Money Model Advisor repo through CLI tools and saved BusinessSnapshot state. Use when advising on Money Models, running the advisor CLI, updating business snapshot facts, searching local Money Models source material, inspecting advisor logs, or producing cited recommendations without provider-key model calls.
---

# Money Model Advisor

Use this skill to operate the repo as a local, subscription-operated Money Models advisor.

Use when the user wants to advise on a real business directory, for example:

```text
Use /path/to/business as the business directory.
```

## Core Rule

Reason conversationally first. Do not route by shallow keywords. Use tools only when they help clarify, calculate, retrieve source material, update state, or inspect prior turns.

Do not use provider-key model calls.

## Business Directory Flow

When the user names a business directory, use that directory as the source of business context and the place where advisor state is saved.

1. Resolve the business directory path.
2. Initialize or refresh local advisor state:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli setup --business-dir /path/to/business
   ```

3. Inspect the saved snapshot:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir /path/to/business
   ```

4. If important context is missing, ask the next useful question in plain English. Do not ask the user to paste JSON.
5. If enough context exists, run an advisor turn with the user's actual request:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir /path/to/business --message "the user's request"
   ```

6. Return the advisor answer in plain English. Mention saved state or logs only when useful.

## Commands

Show saved state:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir /path/to/company
```

Update accepted facts:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli snapshot set --business-dir /path/to/company economics.cac=350
```

Run deterministic math:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli calculate payback --inputs '{"cac":350,"month_one_gp":120,"monthly_recurring_gp":40}'
```

Search local source material:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search "CAC payback period" --layer unit-economics --top-k 5
```

Inspect saved turns:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir /path/to/company
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
