# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The target role is recorded in [JOB_DESCRIPTION.md](JOB_DESCRIPTION.md). That file is the project north star: the repo should demonstrate production-grade AI agent work, RAG judgment, golden datasets, cached embeddings, cost-aware architecture, observability, and regression-oriented evaluation for the Acquisition.com Senior AI Engineer role. Repo-wide Codex guidance lives in [AGENTS.md](AGENTS.md).

The canonical narrative lives in [DESIGN.md](DESIGN.md): it is written like an applied ML paper, with hypotheses, variants, metrics, results, and decisions. [GOLDEN_DATASET.md](GOLDEN_DATASET.md) maps the eval suite to the JD's golden-dataset requirement. [ARCHITECTURE.md](ARCHITECTURE.md) is the technical reference and JD-to-file map. [GLOSSARY.md](GLOSSARY.md) defines common project terms. [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md) defines the advisor's lean state schema. [ADVISOR_QUERY_POLICY_V1.md](ADVISOR_QUERY_POLICY_V1.md) defines runtime retrieval query construction. [AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md](AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md) tracks the current boundary-correction plan. [TOOL_USE_JUDGMENT_PROGRESS.md](TOOL_USE_JUDGMENT_PROGRESS.md) tracks next-action classification, [SOURCE_NEED_GENERATION_PROGRESS.md](SOURCE_NEED_GENERATION_PROGRESS.md) tracks source-need generation, and [SEARCH_QUERY_QUALITY_PROGRESS.md](SEARCH_QUERY_QUALITY_PROGRESS.md) tracks whether source-search queries retrieve useful chunks. [TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md](TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md) defines the concrete eval upgrade. [ADVISOR_RETRIEVAL_HANDOFF.md](ADVISOR_RETRIEVAL_HANDOFF.md) captures the current retrieval trace review and next planner work. [ADVISOR_OPERATING_GUIDE.md](ADVISOR_OPERATING_GUIDE.md) tells an agent how to use the local CLI tools. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the shortcut stack. `evals/reports/` contains the evidence tables behind the narrative.

This repo also includes a small local proof harness so the core modeling decisions can be run with local commands and no external model-service keys.

The next product surface is agent-first and CLI-backed: a human talks to an agent, the agent follows the project skill's guidance, and the agent runs local CLI commands against saved local state. The active project direction does not call external model services.

If the user provides missing information, the agent saves it back into the snapshot. The web app can wait until that loop is actually good.

## Advisor skill

Advisor operation instructions live in the project skill at `.codex/skills/money-model-advisor/SKILL.md`. `AGENTS.md` is for repo-wide development guidance; the skill is for the runtime workflow where an agent uses the CLI to advise a human. Invoke that skill from the folder where advisor context should be saved, then ask the agent naturally. The skill tells the agent how to handle the CLI path plumbing.

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

Search source material from an explicit agent-selected SourceNeed:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  --business-dir /path/to/company \
  --source-need-json '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["CAC","payback period","gross profit"],"user_turn":"why do we need fulfillment cost?"}'
```

Record a completed agent-operated turn:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli turn record \
  --business-dir /path/to/company \
  --user-message "why do we need fulfillment cost?" \
  --assistant-message "Fulfillment cost matters because gross profit, not revenue, pays back CAC." \
  --actions-json '["snapshot","search","answer"]' \
  --source-events-json '[{"source_need":{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["CAC","gross profit"]},"query":"CAC gross profit payback period","chunks":[{"id":"payback-period:0"}]}]' \
  --cited-chunk-ids-json '["payback-period:0"]'
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
  --retrieval-backend bm25 \
  --report evals/reports/advisor_search_query_quality_generated_bm25.md

python3 scripts/compare_retrieval_backends.py --query-source generated \
  --report evals/reports/retrieval_backend_comparison.md

python3 scripts/compare_retrieval_backends.py --query-source generated_variants \
  --report evals/reports/retrieval_backend_comparison_generated_variants.md
```

`compare_retrieval_backends.py` compares BM25, vector, and hybrid retrieval on the same generated-query cases. Vector search uses the OpenAI embeddings API only for vectorization; agent planning, labeling, source-need generation, and answer synthesis remain Codex/CLI operated. Embeddings are cached under `.cache/embeddings/` so repeated runs reuse corpus and query vectors instead of paying for the same inputs again.

Score source-need generation traces:

```bash
python3 scripts/capture_source_need_trace.py prepare sourceneed_v1_001
python3 scripts/capture_source_need_trace.py complete \
  evals/runs/source_need/taxonomy_v2/sourceneed_v1_001 \
  --source-search-decision true \
  --source-need '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["gross profit","fulfillment cost","CAC","payback period"]}'
python3 scripts/eval_source_need_generation.py
```

Score completed source-event traces for search/no-search and multi-search advisor turns:

```bash
python3 scripts/capture_source_event_trace.py prepare sourceevents_v1_001
python3 scripts/capture_source_event_trace.py complete \
  evals/runs/source_events/post_hardening/sourceevents_v1_001 \
  --actions-json '["read_snapshot","calculate","diagnose","search_source_material","search_source_material","turn_record"]' \
  --source-events-json '[{"source_need":{"intent":"diagnostic_evidence","layers":["unit-economics"],"focus_terms":["CAC","payback period"]},"query":"CAC payback period","chunks":[{"id":"payback-period:0"}]},{"source_need":{"intent":"recommendation_evidence","layers":["upsells"],"focus_terms":["upsell","first 30 day gross profit"]},"query":"upsell first 30 day gross profit","chunks":[{"id":"upsells:0"}]}]'
python3 scripts/eval_source_event_traces.py --runs-dir evals/runs/source_events/post_hardening_expanded_v2
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
- Source-event trace eval implemented in `evals/advisor_source_event_cases.jsonl`, with report generation in `scripts/eval_source_event_traces.py`.
- Cached embedding-backed vector retrieval and BM25/vector/hybrid comparison implemented for post-source-need retrieval experiments. BM25 is treated as the lexical baseline/control. The golden search-query slice now has 30 cases; after constrained query variants plus fusion, hybrid is the candidate product path, with continued golden-set validation required before calling it final.
- Agent-facing source-need search implemented in `search --source-need-json`.
- Completed turn persistence implemented in `turn record`.
- Deterministic `chat` orchestration removed from the active product path; the agent owns planning and answer synthesis.
- Core CLI commands implemented: `setup`, `search`, `snapshot`, `calculate`, `diagnose`, `logs`, and `turn record`.
- Advisor operating guide implemented in `ADVISOR_OPERATING_GUIDE.md`, with a project-local skill file in `.codex/skills/money-model-advisor/SKILL.md`.

## What remains planned

- Agent-led local doc inspection before snapshot updates.
- Continue evaluating agent-generated query variants against the golden dataset, while keeping the deterministic flattened query as a baseline/fallback.
- Record latency, cache hits/misses, and cost-oriented signals in retrieval reports.
- Decide whether to add a lightweight vector database adapter or document the production adapter boundary for Pinecone/Qdrant/FAISS/Weaviate.
- Optional LangGraph state graph once the first CLI loop is defined clearly enough to benefit from it.
- Local-only richer evals, CI gates, and trace inspection.
