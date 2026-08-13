# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The target role is recorded in [JOB_DESCRIPTION.md](JOB_DESCRIPTION.md). That file is the project north star: the repo should demonstrate production-grade AI agent work, RAG judgment, golden datasets, cached embeddings, cost-aware architecture, observability, and regression-oriented evaluation for the Acquisition.com Senior AI Engineer role. Repo-wide Codex guidance lives in [AGENTS.md](AGENTS.md).

The portfolio narrative is [narrative.html](narrative.html). [DESIGN.md](DESIGN.md)
is the longer technical decision record, and [GOLDEN_DATASET.md](GOLDEN_DATASET.md)
maps each active evaluation to its data, scorer, and report. Runtime contracts live in
[CLI_DESIGN.md](CLI_DESIGN.md), [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md),
and the project advisor skill. Historical progress files remain in the repo for
reproducibility but do not define current behavior.

This repo also includes a small local proof harness so the core modeling decisions can be run with local commands and no external model-service keys.

The next product surface is agent-first and CLI-backed: a human talks to an agent, the agent follows the project skill's guidance, and the agent runs CLI commands against saved state. Embedding API use is allowed for deterministic vectorization only. Retrieval now has a local/Pinecone vector-store boundary, so a future web-hosted version can reuse the same core.

If the user provides missing information, the agent saves it back into the snapshot. The web app should be a second surface over the same advisor/retrieval core, not a separate implementation.

## Advisor skill

Advisor operation instructions live in the project skill at `.codex/skills/money-model-advisor/SKILL.md`. `AGENTS.md` is for repo-wide development guidance; the skill is for the runtime workflow where an agent uses the CLI to advise a human. Invoke that skill from the folder where advisor context should be saved, then ask the agent naturally. The skill tells the agent how to handle the CLI path plumbing.

## Local proof harness

These commands are for development, verification, debugging, and manual control. During normal use, the human talks to an agent and the skill tells the agent how to run CLI operations such as `read_snapshot`, `update_snapshot`, `calculate`, `search_source_material`, `turn_record`, and `logs`.

Current retrieval uses one corpus-guided query through unfiltered hybrid search over
framework-aware chunks. The 46-case suite tests the raw question and unguided and
guided rewrites through both BM25 and hybrid retrieval; BM25 remains the lexical
control. The selected embedding is `text-embedding-3-large` at 1,536 dimensions,
isolated in its own Pinecone namespace. Local and Pinecone vector stores share the same boundary. The current
remediation work is tracked in [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).

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

Revalidate chunking and the complete frozen query/model/retriever matrix on the
active 46-case suite:

```bash
python3 scripts/revalidate_retrieval_choices.py chunking
python3 scripts/revalidate_retrieval_choices.py matrix
```

The matrix report compares the raw question, unguided rewrite, and corpus-guided
rewrite conditions through BM25 and hybrid retrieval over the final framework-aware
chunks. See `evals/reports/active_framework_retrieval_matrix.md`.

Index and benchmark the active Pinecone path:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli index pinecone \
  --chunking framework-aware \
  --namespace money-models-framework-large-d1536

python3 scripts/revalidate_retrieval_choices.py pinecone \
  --chunking framework-aware \
  --policy single \
  --single-namespace money-models-framework-large-d1536 \
  --max-workers 1 \
  --summary evals/reports/pinecone_large_embedding_revalidation_summary.json \
  --cases-output evals/reports/pinecone_large_embedding_revalidation_cases.jsonl
```

Pinecone runs require `PINECONE_API_KEY` and `PINECONE_INDEX_HOST`. Embeddings are
used only for deterministic vectorization and cached under `.cache/embeddings/`.

The current hosted benchmark uses the active 46-case, one-query path, framework-aware chunks, and `text-embedding-3-large` at 1,536 dimensions. The isolated unfiltered namespace reaches 93.5% Hit@1, 100% Hit@5, and 86.1% Useful@5 at 1.13s p50 / 1.43s p95. The earlier namespace experiment did not improve quality, and removing a redundant 10x vector over-fetch reduced latency without changing rankings. See `evals/reports/pinecone_large_embedding_revalidation.md` and `evals/reports/pinecone_candidate_depth_optimization.md`.

The older orchestration model-routing harness remains available for historical
replay. It uses `codex exec`, lets the model operate the CLI, and does not use
`OPENAI_API_KEY`:

```bash
python3 scripts/eval_codex_model_routing.py
# subset/smoke: --suites source_need --limit 2
# traces are cached under evals/runs/model_routing_codex/; --force re-runs them
```

The report lands at `evals/reports/model_routing_tiering.md`. It predates the current
single-query contract and should not be used as query-writer evidence.

Replay the retired source-need planning experiment:

```bash
python3 scripts/capture_source_need_trace.py prepare sourceneed_v1_001
python3 scripts/capture_source_need_trace.py complete \
  evals/runs/source_need/taxonomy_v2/sourceneed_v1_001 \
  --source-search-decision true \
  --source-need '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["gross profit","fulfillment cost","CAC","payback period"]}'
python3 scripts/eval_source_need_generation.py
```

Run and score the current source-event regression for search/no-search and
multi-search advisor turns:

```bash
python3 scripts/run_source_event_codex_eval.py --max-workers 2
python3 scripts/eval_source_event_traces.py
python3 scripts/eval_advisor_answer_quality.py
```

The runner gives each isolated acting agent the case context but hides the expected
labels. The scorer checks the active single-query `SearchRequest` contract and writes
`evals/reports/advisor_source_event_traces.md`.

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
- The retired source-need eval remains reproducible from
  `evals/advisor_source_need_cases.jsonl` and
  `scripts/eval_source_need_generation.py`; it is not the active query contract.
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
- Continue monitoring hosted-vector tail latency as the corpus and traffic grow.
- Optional LangGraph state graph once the CLI advisor loop is defined clearly enough to benefit from it.
- Final hiring write-up assembled from the narrative, reports, and saved result tables.
