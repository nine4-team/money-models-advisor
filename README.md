# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The canonical narrative lives in [DESIGN.md](DESIGN.md): it is written like an applied ML paper, with hypotheses, variants, metrics, results, and decisions. [ARCHITECTURE.md](ARCHITECTURE.md) is the technical reference and JD-to-file map. [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md) defines the advisor's lean state schema. [ADVISOR_QUERY_POLICY_V1.md](ADVISOR_QUERY_POLICY_V1.md) defines runtime retrieval query construction. [ADVISOR_OPERATING_GUIDE.md](ADVISOR_OPERATING_GUIDE.md) tells a subscription-operated advisor how to use the local CLI tools. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the shortcut stack. `evals/reports/` contains the evidence tables behind the narrative.

This repo also includes a small local proof harness so the core modeling decisions can be run with local commands and no provider keys.

The next product surface is CLI-first and subscription-operated: run setup/intake to build a `BusinessSnapshot`, then use Codex/ChatGPT subscription context to operate the advisor over CLI tools and saved local state. The active project direction does not use provider-key model calls.

If the user provides missing information during chat, the advisor saves it back into the snapshot. The web app can wait until that loop is actually good.

## Agent quickstart

For a natural-language agent run, open this repo and point the agent at the real business directory:

```text
Use ../1584-design as the business directory and tell me what to fix first.
```

The root `AGENTS.md` tells the agent to initialize or refresh `.money-model-advisor/` in that business directory, inspect the saved `BusinessSnapshot`, ask for missing facts in plain English, and run the local `chat` command when enough context exists.

## Local proof harness

Set up advisor state for a business directory:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli setup \
  --business-dir /path/to/company \
  --interactive
```

Or provide repeatable setup answers as JSON:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli setup \
  --business-dir /path/to/company \
  --answers '{"business":{"business_type":"coaching business","icp":"gym owners"},"money_model":{"core_offer":{"description":"implementation program","price":5000},"attraction_offer":{"exists":true},"upsell":{"exists":false},"downsell":{"exists":true},"continuity":{"exists":false}},"economics":{"cac":350,"first_30_day_gross_profit":120},"problem":{"user_goal":"diagnose cash payback"}}'
```

Run one advisor turn from the saved snapshot:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli chat \
  --business-dir /path/to/company \
  --message "We are a coaching business. Core offer is implementation program. CAC is $350 and first-30-day gross profit is $120. I want to diagnose cash payback."
```

The CLI writes local state under `/path/to/company/.money-model-advisor/`.

Run deterministic calculations:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli calculate gross-margin \
  --inputs '{"price":100,"cogs":20}'
```

Diagnose a business snapshot:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli diagnose \
  --snapshot '{"cac":200,"first_30_day_gross_profit":80,"monthly_recurring_gross_profit":20,"lifetime_gross_profit":250,"gross_margin":0.4}'
```

Search the transcript corpus through the five-layer local taxonomy:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  "When should I use a rollover upsell?" --layer upsells
```

Show or update the saved business snapshot:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli snapshot \
  --business-dir /path/to/company

PYTHONPATH=src python3 -m money_model_architect.cli snapshot set \
  --business-dir /path/to/company \
  economics.cac=350 \
  money_model.upsell.exists=false
```

Inspect saved advisor logs:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli logs \
  --business-dir /path/to/company
```

Run the smoke eval:

```bash
PYTHONPATH=src python3 scripts/eval_smoke.py
python3 -m unittest discover -s tests -v
```

Generate the local retrieval baseline report:

```bash
PYTHONPATH=src python3 scripts/eval_retrieval.py
```

Compare chunking strategies:

```bash
PYTHONPATH=src python3 scripts/compare_chunking.py
```

Audit query realism before final retriever selection:

```bash
PYTHONPATH=src python3 scripts/audit_query_realism.py
```

Review human-auditable required-claim labels:

```bash
PYTHONPATH=src python3 scripts/review_obligations.py
```

Score required-claim support coverage:

```bash
PYTHONPATH=src python3 scripts/score_obligation_support.py --include-proposed
PYTHONPATH=src python3 scripts/score_obligation_support.py
```

## What is implemented now

- Five-layer namespace taxonomy with primary and secondary chapter roles.
- Standard-library local retrieval over transcript chunks.
- Deterministic CAC, gross profit, gross margin, LTGP, CFA level, and payback formulas.
- Constraint diagnosis that follows the coach diagnostic flow.
- A 32-query pilot retrieval set.
- A draft realistic user-intent query set in `evals/realistic_queries.jsonl`, documented in `evals/reports/query_realism.md`.
- A local retrieval baseline report in `evals/reports/local_retrieval_baseline.md`.
- A chunking comparison report in `evals/reports/chunking_comparison.md`; `heading-aware` remains the default, while `framework-aware` is tracked as a candidate.
- A 65-label reviewed required-claim support set in `evals/obligations.jsonl`, plus a local review UI in `scripts/review_obligations.py`.
- A required-claim support scorer in `scripts/score_obligation_support.py`; accepted-label BM25 heading-aware coverage is currently 87.69%.
- A corrected architecture direction for setup/intake plus snapshot-backed chat.
- `BusinessSnapshot v1` implemented in `src/money_model_architect/snapshot.py`.
- Setup/intake state directory and manifest hashing implemented in `src/money_model_architect/business_context.py`.
- Setup/intake answer collection implemented in `src/money_model_architect/setup_intake.py`.
- Advisor runtime query policy implemented in `src/money_model_architect/advisor_queries.py`.
- Advisor query execution and local evidence capture implemented in `src/money_model_architect/advisor_retrieval.py`.
- First stateful advisor turn implemented in `src/money_model_architect/advisor.py`, with `setup`, `chat`, `search`, `snapshot`, and `logs` CLI commands.
- Visible `chat` answer synthesis started: diagnosis, key math, recommendation, source chunk IDs, and next action.
- Advisor operating guide implemented in `ADVISOR_OPERATING_GUIDE.md`, with a project-local skill file in `.codex/skills/money-model-advisor/SKILL.md`.

## What remains planned

- Broader answer synthesis for teach/compare/clarify/recommendation cases.
- Setup/intake fact collection from user answers and optional local files.
- Snapshot extraction and next-action eval reports.
- Optional LangGraph state graph once the first CLI loop is defined clearly enough to benefit from it.
- Local-only richer evals, CI gates, and trace inspection.
