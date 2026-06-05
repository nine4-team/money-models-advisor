---
name: money-model-advisor
description: Help a human with Money Models by using this skill's guidance to run the Money Model Advisor CLI. Use when advising on Money Models, updating saved BusinessSnapshot facts, searching local Money Models source material, inspecting advisor logs, or producing cited recommendations without external model-service calls.
---

# Money Model Advisor

Use this skill when a human asks an agent for Money Models advice. The agent talks with the human, follows this skill's guidance to run the CLI, and the CLI reads from and writes to local advisor state.

The human should experience this as a normal conversation, not as a CLI workflow.

## Core Rule

Reason conversationally first. Do not route by shallow keywords.

Every human advisory request must run the CLI `chat` command before the final answer so the turn is persisted. Use additional CLI tools only when they help clarify, calculate, search source material, update state, or inspect prior turns.

Do not call external model services.

## Path Resolution

The user should not have to understand path plumbing. Resolve paths this way:

- `advisor_repo`: `/Users/benjaminmackenzie/Dev/money-model-architect`
- `context_dir`: the current working directory when the skill is invoked; this is where advisor state is read and written

Run CLI commands from `advisor_repo` and pass `context_dir` to the CLI's `--business-dir` flag.

The CLI flag is an implementation detail. Do not ask the human to reason about `--business-dir`.

## Mental Model

```text
human asks agent for advice
-> agent follows this skill's guidance
-> agent runs local CLI commands
-> CLI reads/writes .money-model-advisor/ in context_dir
-> agent answers the human in plain English
```

The folder where the skill is invoked is the context directory. It is where advisor state is saved. It is not automatically something to analyze.

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

4. Run an advisor turn with the human's actual request, even if the snapshot is incomplete:

   ```bash
   cd /Users/benjaminmackenzie/Dev/money-model-architect
   USER_REQUEST=$(cat <<'EOF'
   the human's exact request
   EOF
   )
   PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir "$CONTEXT_DIR" --message "$USER_REQUEST"
   ```

   Use the quoted heredoc exactly as shown when the request contains dollar amounts. Do not put a literal money-containing request in double quotes, because the shell can expand values like `$500`.

   The `chat` command persists the turn. If context is missing, it should return the next useful clarifying question and save the trace.

5. Return the advisor answer in plain English. Mention saved state or logs only when useful.
6. If the human provides a clear fact outside a `chat` turn, save it with `snapshot set`. If the same human message also asks for advice, run `chat` after `snapshot set` before answering. Only pure fact-update or admin turns may skip `chat`.

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
2. Run `chat` for the human's advisory request so the turn is persisted.
3. Let `chat` ask for missing context when the snapshot is insufficient.
4. Save clear user-provided facts with `snapshot set` when they are provided outside a `chat` turn.
5. Use `calculate` for payback, CAC, gross profit, gross margin, LTGP, and CFA level.
6. Use `search` when teaching, comparing, diagnosing, or recommending needs source support.
7. Cite inspected chunks inline, such as `[payback-period:0]`.
8. Use `logs` to inspect prior session turns.

## Guardrails

- Do not save guesses as snapshot facts.
- Do not reread local business files during chat; use `BusinessSnapshot`.
- Do not cite chunks you did not inspect.
- Do not turn every user message into retrieval.
- Prefer one clear clarifying question over premature recommendation.
