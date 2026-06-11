# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The canonical narrative lives in [DESIGN.md](DESIGN.md): it is written like an applied ML paper, with hypotheses, variants, metrics, results, and decisions. [ARCHITECTURE.md](ARCHITECTURE.md) is the technical reference and JD-to-file map. [GLOSSARY.md](GLOSSARY.md) defines common project terms. [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md) defines the advisor's lean state schema. [ADVISOR_QUERY_POLICY_V1.md](ADVISOR_QUERY_POLICY_V1.md) defines runtime retrieval query construction. [AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md](AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md) tracks the current boundary-correction plan. [TOOL_USE_JUDGMENT_PROGRESS.md](TOOL_USE_JUDGMENT_PROGRESS.md) tracks next-action classification, [SOURCE_NEED_GENERATION_PROGRESS.md](SOURCE_NEED_GENERATION_PROGRESS.md) tracks source-need generation, and [SEARCH_QUERY_QUALITY_PROGRESS.md](SEARCH_QUERY_QUALITY_PROGRESS.md) tracks whether source-search queries retrieve useful chunks. [TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md](TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md) defines the concrete eval upgrade. [ADVISOR_RETRIEVAL_HANDOFF.md](ADVISOR_RETRIEVAL_HANDOFF.md) captures the current retrieval trace review and next planner work. [ADVISOR_OPERATING_GUIDE.md](ADVISOR_OPERATING_GUIDE.md) tells an agent how to use the local CLI tools. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the shortcut stack. `evals/reports/` contains the evidence tables behind the narrative.

This repo also includes a small local proof harness so the core modeling decisions can be run with local commands and no external model-service keys.

The next product surface is agent-first and CLI-backed: a human talks to an agent, the agent follows the project skill's guidance, and the agent runs local CLI commands against saved local state. The active project direction does not call external model services.

If the user provides missing information, the agent saves it back into the snapshot. The web app can wait until that loop is actually good.

## Advisor skill

Advisor operation instructions live in the project skill at `.codex/skills/money-model-advisor/SKILL.md`. Invoke that skill from the folder where advisor context should be saved, then ask the agent naturally. The skill tells the agent how to handle the CLI path plumbing.

## Local proof harness

These commands are for development, verification, debugging, and manual control. During normal use, the human talks to an agent and the skill tells the agent how to run CLI operations such as `read_snapshot`, `update_snapshot`, `calculate`, `search_source_material`, `turn_record`, and `logs`.

Current dev focus: repair the agent/CLI boundary before adding retrieval complexity. The project keeps the ladder separate: first, next-action classification asks whether the next action should be source-material search, saved-state read, local-doc inspection, calculation, clarification, saved-context update, or direct answer. Second, source-need generation asks what source support is needed when search is appropriate. Third, search-query quality asks whether that source need retrieves useful Money Models chunks. The current boundary-refactor plan is in `AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md`.

Set up advisor state for a context directory:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli setup \
  --business-dir /path/to/company \
  --interactive
```

For proof-harness tests, setup can accept repeatable answers as JSON. In normal use, the agent should save accepted facts with `update_snapshot` after inspecting docs or talking with the human:

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

Score source-search query quality on search-appropriate turns. Reference mode scores reviewer-authored source-specific queries; generated mode scores the current runtime query builder using the same cases and their advisor-selected source needs:

```bash
python3 scripts/eval_search_query_quality.py --query-source reference \
  --report evals/reports/advisor_search_query_quality.md

python3 scripts/eval_search_query_quality.py --query-source generated \
  --report evals/reports/advisor_search_query_quality_generated.md
```

Score source-need generation traces:

```bash
python3 scripts/capture_source_need_trace.py prepare sourceneed_v1_001
python3 scripts/capture_source_need_trace.py complete \
  evals/runs/source_need/pilot/sourceneed_v1_001 \
  --source-search-decision true \
  --source-need '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["gross profit","fulfillment cost","CAC","payback period"]}'
python3 scripts/eval_source_need_generation.py
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
- A corrected architecture direction for setup/intake plus snapshot-backed agent operation.
- `BusinessSnapshot v1` implemented in `src/money_model_architect/snapshot.py`.
- Setup/intake state directory implemented in `src/money_model_architect/business_context.py`.
- Setup/intake answer collection implemented in `src/money_model_architect/setup_intake.py`.
- Advisor runtime query policy implemented in `src/money_model_architect/advisor_queries.py`.
- Advisor query execution and local evidence capture implemented in `src/money_model_architect/advisor_retrieval.py`.
- Source-search query quality eval implemented in `evals/advisor_search_query_cases.jsonl`, with reference-query and generated-query reports in `evals/reports/`.
- Source-need generation eval implemented in `evals/advisor_source_need_cases.jsonl`, with report generation in `scripts/eval_source_need_generation.py`.
- Deterministic stateful advisor prototype implemented in `src/money_model_architect/advisor.py`; this is being replaced in the product path by agent-led tool use plus `turn record`.
- Core CLI commands started: `setup`, `search`, `snapshot`, and `logs`; `turn record` and source-need search are next.
- Advisor operating guide implemented in `ADVISOR_OPERATING_GUIDE.md`, with a project-local skill file in `.codex/skills/money-model-advisor/SKILL.md`.

## What remains planned

- Agent/CLI boundary refactor: add `turn record`, add source-need search, and remove deterministic advisor orchestration from the product path.
- Agent-led local doc inspection before snapshot updates.
- Source-need taxonomy and scoring cleanup before retrieval-model comparisons.
- Optional LangGraph state graph once the first CLI loop is defined clearly enough to benefit from it.
- Local-only richer evals, CI gates, and trace inspection.
