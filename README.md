# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The target role is recorded in [JOB_DESCRIPTION.md](JOB_DESCRIPTION.md). That file is the project north star: the repo should demonstrate production-grade AI agent work, RAG judgment, golden datasets, cached embeddings, cost-aware architecture, observability, and regression-oriented evaluation for the Acquisition.com Senior AI Engineer role. Repo-wide Codex guidance lives in [AGENTS.md](AGENTS.md).

The canonical narrative lives in [DESIGN.md](DESIGN.md): it is written like an applied ML paper, with hypotheses, variants, metrics, results, and decisions. [JOB_DESCRIPTION.md](JOB_DESCRIPTION.md) records the target role, and [JD_REQUIREMENTS_AUDIT.md](JD_REQUIREMENTS_AUDIT.md) maps each JD requirement to current evidence, gaps, and next proof. [GOLDEN_DATASET.md](GOLDEN_DATASET.md) maps the eval suite to the JD's golden-dataset requirement. [ARCHITECTURE.md](ARCHITECTURE.md) is the technical reference and JD-to-file map. [CLI_DESIGN.md](CLI_DESIGN.md) defines the agent-operated CLI product contract. [GLOSSARY.md](GLOSSARY.md) defines common project terms. [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md) defines the advisor's lean state schema. [ADVISOR_QUERY_POLICY_V1.md](ADVISOR_QUERY_POLICY_V1.md) defines runtime retrieval query construction. [AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md](AGENT_CLI_BOUNDARY_REFACTOR_PLAN.md) tracks the boundary-correction history. [TOOL_USE_JUDGMENT_PROGRESS.md](TOOL_USE_JUDGMENT_PROGRESS.md) tracks next-action classification, [SOURCE_NEED_GENERATION_PROGRESS.md](SOURCE_NEED_GENERATION_PROGRESS.md) tracks source-need generation, and [SEARCH_QUERY_QUALITY_PROGRESS.md](SEARCH_QUERY_QUALITY_PROGRESS.md) tracks whether source-search queries retrieve useful chunks. [TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md](TOOL_USE_EVAL_IMPLEMENTATION_PLAN.md) defines the concrete eval upgrade. [ADVISOR_RETRIEVAL_HANDOFF.md](ADVISOR_RETRIEVAL_HANDOFF.md) captures the current retrieval trace review and next planner work. [ADVISOR_OPERATING_GUIDE.md](ADVISOR_OPERATING_GUIDE.md) tells an agent how to use the local CLI tools. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the shortcut stack. `evals/reports/` contains the evidence tables behind the narrative.

This repo also includes a small local proof harness so the core modeling decisions can be run with local commands and no external model-service keys.

The next product surface is agent-first and CLI-backed: a human talks to an agent, the agent follows the project skill's guidance, and the agent runs CLI commands against saved state. Embedding API use is allowed for deterministic vectorization only. Retrieval now has a local/Pinecone vector-store boundary, so a future web-hosted version can reuse the same core.

If the user provides missing information, the agent saves it back into the snapshot. The web app should be a second surface over the same advisor/retrieval core, not a separate implementation.

## Advisor skill

Advisor operation instructions live in the project skill at `.codex/skills/money-model-advisor/SKILL.md`. `AGENTS.md` is for repo-wide development guidance; the skill is for the runtime workflow where an agent uses the CLI to advise a human. Invoke that skill from the folder where advisor context should be saved, then ask the agent naturally. The skill tells the agent how to handle the CLI path plumbing.

## Local proof harness

These commands are for development, verification, debugging, and manual control. During normal use, the human talks to an agent and the skill tells the agent how to run CLI operations such as `read_snapshot`, `update_snapshot`, `calculate`, `search_source_material`, `turn_record`, and `logs`.

Current dev focus: turn the working agent-operated CLI pieces into an impressive end-to-end advisor workflow. The project keeps the evaluation ladder separate: first, next-action classification asks whether the next action should be source-material search, saved-state read, local-doc inspection, calculation, clarification, saved-context update, or direct answer. Second, source-need generation asks what source support is needed when search is appropriate. Third, search-query quality asks whether that source need retrieves useful Money Models chunks. Retrieval now has local and Pinecone-backed vector storage; the next product-facing work is making the CLI session flow crisp, traceable, and demo-ready.

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

Start an agent-operated advisor turn:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli session start \
  --business-dir /path/to/company \
  --user-message "what should we do next?"
```

Search source material from one explicit corpus-guided request:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  --business-dir /path/to/company \
  --search-request-json '{"intent":"teaching_evidence","user_turn":"why do we need fulfillment cost?","query":"fulfillment cost gross profit customer acquisition cost payback period"}'
```

Record a completed agent-operated turn:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli session finish \
  --business-dir /path/to/company \
  --record-json /path/to/turn-record.json
```

The CLI writes local state under `/path/to/company/.money-model-advisor/`.

Run deterministic calculations:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli calculate gross-margin \
  --inputs '{"price":100,"cogs":20}'
```

Diagnose saved advisor state:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli diagnose \
  --business-dir /path/to/company
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

Pinecone-backed retrieval uses the same generated-query cases after the corpus has been indexed:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli index pinecone

python3 scripts/compare_retrieval_backends.py --query-source generated_variants \
  --vector-store pinecone \
  --report evals/reports/retrieval_backend_comparison_generated_variants_pinecone.md
```

Pinecone runs require `PINECONE_API_KEY` and `PINECONE_INDEX_HOST`. Local tests and local evals continue to use `--vector-store local`.

The JD-specific multi-namespace experiment indexes the same corpus into the five Money Models layer namespaces and runs an oracle namespace condition where `SourceNeed.target_namespaces` is populated from expected layers:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli index pinecone \
  --index-layout layer \
  --namespace-prefix money-models

python3 scripts/compare_retrieval_backends.py --query-source generated_variants \
  --vector-store local \
  --target-namespace-source expected_layers \
  --report evals/reports/retrieval_backend_comparison_generated_variants_local_layer_namespaces_oracle.md

python3 scripts/compare_retrieval_backends.py --query-source generated_variants \
  --vector-store pinecone \
  --target-namespace-source expected_layers \
  --max-workers 8 \
  --report evals/reports/retrieval_backend_comparison_generated_variants_pinecone_layer_namespaces_oracle.md
```

The current hosted benchmark uses the active 46-case, one-query path and framework-aware chunks. A single unfiltered namespace preserves 93.5% Hit@1 and 100% Hit@5 at 4.07s p50 and 7.64s p95. An oracle subject split does not improve the hit-rate cutoffs and worsens p95 to 10.47s, so the runtime keeps one namespace and treats hosted latency optimization as open work. See `evals/reports/active_query_pinecone_revalidation.md`.

Run the product-harness model-routing baseline. This uses `codex exec`, so the model acts as an agent, can run the local CLI, and writes normal trace artifacts. It does not use `OPENAI_API_KEY`:

```bash
python3 scripts/eval_codex_model_routing.py
# subset/smoke: --suites source_need --limit 2
# traces are cached under evals/runs/model_routing_codex/; --force re-runs them
```

The report lands at `evals/reports/model_routing_tiering.md` with a summary JSON beside it. The current corrected decision: `gpt-5.5` via Codex CLI is the OpenAI agent baseline; no cheaper Codex tier is promoted because the attempted `gpt-5-mini` Codex run is unsupported for this ChatGPT subscription harness. API replay can still be used as a separately labeled provider experiment, but not as the product-routing result.

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
  --source-events-json '[{"search_request":{"intent":"diagnostic_evidence","user_turn":"what should we fix first?","query":"client financed acquisition CAC gross profit payback period"},"query":"client financed acquisition CAC gross profit payback period","chunks":[{"id":"payback-period:0"}]},{"search_request":{"intent":"recommendation_evidence","user_turn":"what should we fix first?","query":"upsell offers first 30 day gross profit payback"},"query":"upsell offers first 30 day gross profit payback","chunks":[{"id":"upsells:0"}]}]'
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
- Chunking comparison and active-path revalidation reports; `framework-aware` is the runtime default after preserving 100% Hit@5 while eliminating multi-thousand-word heading chunks.
- A 65-label reviewed required-claim support set in `evals/obligations.jsonl`, plus a local review UI in `scripts/review_obligations.py`.
- A required-claim support scorer in `scripts/score_obligation_support.py`; accepted-label BM25 heading-aware coverage is currently 87.69%.
- A corrected architecture direction for setup/intake plus snapshot-backed agent operation.
- `BusinessSnapshot v1` implemented in `src/money_model_architect/snapshot.py`.
- Setup/intake state directory implemented in `src/money_model_architect/business_context.py`.
- Setup/intake answer collection implemented in `src/money_model_architect/setup_intake.py`.
- Advisor runtime single-query policy implemented in `src/money_model_architect/advisor_queries.py`.
- Advisor query execution and local evidence capture implemented in `src/money_model_architect/advisor_retrieval.py`.
- Source-search query quality eval implemented in `evals/advisor_search_query_cases.jsonl`, with reference-query and generated-query reports in `evals/reports/`.
- Source-need generation eval implemented in `evals/advisor_source_need_cases.jsonl`, with report generation in `scripts/eval_source_need_generation.py`.
- Source-event trace eval implemented in `evals/advisor_source_event_cases.jsonl`, with report generation in `scripts/eval_source_event_traces.py`.
- Cached embedding-backed vector retrieval and BM25/vector/hybrid comparison implemented. BM25 is the lexical control. The active path uses one corpus-guided query with unfiltered hybrid retrieval; the approach leads the 46-case audited regression suite, and the hybrid-backend decision holds under both tested query writers.
- Agent-facing single-query search implemented in `search --search-request-json`; the older `--source-need-json` remains only for reproducing historical evals and manual debugging.
- Agent-facing session workbench implemented in `session start`; it loads state, recent traces, known/missing facts, operation names, and trace requirements without synthesizing an answer.
- Agent-facing completed turn persistence implemented in `session finish`; lower-level `turn record` remains available for tests and scripts.
- Deterministic `chat` orchestration removed from the active product path; the agent owns planning and answer synthesis.
- Core CLI commands implemented: `setup`, `session start`, `session finish`, `search`, `snapshot`, `calculate`, `diagnose`, `logs`, and `turn record`.
- Advisor operating guide implemented in `ADVISOR_OPERATING_GUIDE.md`, with a project-local skill file in `.codex/skills/money-model-advisor/SKILL.md`.

## What remains planned

- Agent-led local doc inspection before snapshot updates.
- Optimize hosted-vector latency now that Pinecone indexing and parity evals are working.
- Optional LangGraph state graph once the CLI advisor loop is defined clearly enough to benefit from it.
- Final hiring write-up assembled from the narrative, reports, and saved result tables.
