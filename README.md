# Money Model Architect

A portfolio RAG and diagnostic advisor for Alex Hormozi's *$100M Money Models*.

The canonical narrative lives in [DESIGN.md](DESIGN.md): it is written like an applied ML paper, with hypotheses, variants, metrics, results, and decisions. [ARCHITECTURE.md](ARCHITECTURE.md) is the technical reference and JD-to-file map. [BUSINESS_SNAPSHOT_V1.md](BUSINESS_SNAPSHOT_V1.md) defines the advisor's lean state schema. [ADVISOR_QUERY_POLICY_V1.md](ADVISOR_QUERY_POLICY_V1.md) defines runtime retrieval query construction. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the shortcut stack. `evals/reports/` contains the evidence tables behind the narrative.

This repo also includes a small local proof harness so the core modeling decisions can be run without Pinecone or a web service. API-backed embedding experiments use OpenAI embeddings when `OPENAI_API_KEY` is present, and cache results locally to avoid paying for the same corpus/query embeddings repeatedly.

The next product surface is CLI-first and subscription-operated: run setup/intake to build a `BusinessSnapshot`, then use Codex/ChatGPT subscription context to operate the advisor over CLI tools and saved local state. The advisor runtime is not planned as an OpenAI API agent loop for v1. API calls remain optional for offline retrieval experiments, not for the main advisor conversation.

If the user provides missing information during chat, the advisor saves it back into the snapshot. The web app can wait until that loop is actually good.

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

Search the transcript corpus through the same five-layer taxonomy planned for Pinecone:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  "When should I use a rollover upsell?" --layer upsells
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

Run API-backed retrieval ablation and required-claim support guardrail:

```bash
PYTHONPATH=src python3 scripts/retrieval_ablation.py
PYTHONPATH=src python3 scripts/retrieval_required_claim_ablation.py
```

Audit query realism before final retriever selection:

```bash
PYTHONPATH=src python3 scripts/audit_query_realism.py
```

Build, review, and score blind chunk relevance labels:

```bash
PYTHONPATH=src python3 scripts/build_chunk_relevance_pool.py
PYTHONPATH=src python3 scripts/review_chunk_relevance.py --port 8766
PYTHONPATH=src python3 scripts/score_chunk_relevance.py
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
- A blind chunk relevance pool in `evals/chunk_relevance_pool.jsonl`, with a review UI in `scripts/review_chunk_relevance.py` and scorer in `scripts/score_chunk_relevance.py`.
- A local retrieval baseline report in `evals/reports/local_retrieval_baseline.md`.
- A chunking comparison report in `evals/reports/chunking_comparison.md`; `heading-aware` remains the default, while `framework-aware` is tracked as a candidate.
- A 65-label reviewed required-claim support set in `evals/obligations.jsonl`, plus a local review UI in `scripts/review_obligations.py`.
- A required-claim support scorer in `scripts/score_obligation_support.py`; accepted-label BM25 heading-aware coverage is currently 87.69%.
- An OpenAI embeddings retrieval ablation in `evals/reports/retrieval_ablation.md`; useful as a pilot comparison, but not final retrieval-selection evidence because it uses chapter-level labels.
- A required-claim retrieval ablation in `evals/reports/retrieval_required_claim_ablation.md`; useful as a support sanity check, but not final retrieval-selection evidence because the support chunks are not exhaustive.
- A SQLite embedding cache in `.cache/embeddings.sqlite3`, keyed by model and text hash, so rerunning retrieval ablations reuses deterministic embeddings instead of making duplicate API calls.
- A corrected architecture direction for setup/intake plus snapshot-backed chat.
- `BusinessSnapshot v1` implemented in `src/money_model_architect/snapshot.py`.
- Setup/intake state directory and manifest hashing implemented in `src/money_model_architect/business_context.py`.
- Setup/intake answer collection implemented in `src/money_model_architect/setup_intake.py`.
- Advisor runtime query policy implemented in `src/money_model_architect/advisor_queries.py`.
- Advisor query execution and local evidence capture implemented in `src/money_model_architect/advisor_retrieval.py`.
- First stateful advisor turn implemented in `src/money_model_architect/advisor.py`, with `setup` and `chat` CLI commands.

## What remains planned

- Recommendation synthesis that uses captured evidence chunks in the visible advisor answer.
- Setup/intake fact collection from user answers and optional local files.
- Snapshot extraction and next-action eval reports.
- Dense + sparse hybrid retrieval with RRF and reranking where chunk-level relevance evaluation shows it earns the complexity.
- Optional LangGraph state graph once the first CLI loop is defined clearly enough to benefit from it.
- Model-routing reports, richer evals, CI gates, observability, and dashboard.
