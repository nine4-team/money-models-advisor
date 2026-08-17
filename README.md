# Money Model Architect

An agent-operated, CLI-backed advisor for applying the frameworks in Alex Hormozi's
*$100M Money Models*. This repository is a portfolio artifact for the Acquisition.com
Senior AI Engineer role described in [JOB_DESCRIPTION.md](JOB_DESCRIPTION.md).

The fastest way to review the project is:

1. Open [narrative.html](narrative.html) for the design story and measured decisions.
2. Read [DESIGN.md](DESIGN.md) for the current architecture.
3. Read [GOLDEN_DATASET.md](GOLDEN_DATASET.md) for the dataset-to-risk map.
4. Run `python3 scripts/regression_gate.py` for the stable offline checks.

## Architecture

```text
human talks to agent
-> agent decides the next action and writes any search request
-> CLI persists state, calculates, retrieves, and records traces
-> agent inspects the evidence and answers
```

The agent owns semantic judgment: next action, query content, passage usefulness,
accepted memory updates, and final-answer quality. The CLI owns deterministic work:
state persistence, formulas, retrieval execution, embedding-cache use, trace
validation, and report generation.

The selected retrieval path is one corpus-guided, unfiltered query through hybrid
retrieval over framework-aware chunks. It uses cached `text-embedding-3-large`
vectors at 1,536 dimensions. Pinecone sits behind the same retrieval boundary as the
local evaluation backend. BM25 remains a lexical control, not the product default.

## Setup

Python 3.11 or newer is required. The offline tests have no third-party package
dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

The installed command is `mma` (also available as `money-model-advisor`). Commands
below use `mma`; `PYTHONPATH=src python3 -m money_model_architect.cli` is equivalent.

Initialize a business context:

```bash
mma setup --business-dir /path/to/company --interactive
```

Start an agent-operated turn:

```bash
mma session start \
  --business-dir /path/to/company \
  --user-message "what should we do next?"
```

Run a structured search:

```bash
mma search \
  --business-dir /path/to/company \
  --search-request-json \
  '{"intent":"teaching_evidence","user_turn":"why do we need fulfillment cost?","query":"fulfillment cost gross profit customer acquisition cost payback period"}'
```

Run deterministic math:

```bash
mma calculate payback \
  --inputs '{"cac":350,"month_one_gp":120,"monthly_recurring_gp":40}'
```

State and traces are written under
`/path/to/company/.money-model-advisor/`, which is ignored by Git.

## Verification

Run the stable offline gate:

```bash
python3 scripts/regression_gate.py
```

It runs unit tests, the local retrieval smoke test, strict saved-artifact scorers for
tool use, source events, calculations, and answer quality, the narrative evidence
drift check, and patch hygiene. It does not call an acting model, embedding API, or
hosted vector store.

Reproduce the active retrieval matrix from frozen queries and cached embeddings:

```bash
python3 scripts/revalidate_retrieval_choices.py chunking
python3 scripts/revalidate_retrieval_choices.py matrix
```

Hosted Pinecone replay requires `PINECONE_API_KEY` and `PINECONE_INDEX_HOST`:

```bash
mma index pinecone \
  --chunking framework-aware \
  --namespace money-models-framework-large-d1536

python3 scripts/revalidate_retrieval_choices.py pinecone \
  --chunking framework-aware \
  --policy single \
  --single-namespace money-models-framework-large-d1536 \
  --max-workers 1
```

## Current evidence

- Query/retrieval matrix: [active_framework_retrieval_matrix.md](evals/reports/active_framework_retrieval_matrix.md)
- Chunking revalidation: [active_query_chunking_revalidation.md](evals/reports/active_query_chunking_revalidation.md)
- Embedding comparison: [embedding_model_comparison.md](evals/reports/embedding_model_comparison.md)
- Pinecone replay: [pinecone_large_embedding_revalidation.md](evals/reports/pinecone_large_embedding_revalidation.md)
- Search-decision models: [search_decision_model_comparison.md](evals/reports/search_decision_model_comparison.md)
- Source-event traces: [advisor_source_event_traces.md](evals/reports/advisor_source_event_traces.md)
- Answer quality: [advisor_answer_quality_expanded.md](evals/reports/advisor_answer_quality_expanded.md)

Current reports live directly under `evals/reports/`. Superseded experiments are
labeled and retained under `evals/reports/archive/`; completed planning records live
under `docs/history/`.

## Repository map

| Path | Purpose |
|---|---|
| `.codex/skills/money-model-advisor/` | Agent operating instructions |
| `src/money_model_architect/` | CLI, state, calculations, retrieval, and trace validation |
| `corpus/` | Source material and corpus guide inputs |
| `evals/` | Golden cases, saved runs, and reports |
| `scripts/` | Active evaluation and reproducibility commands |
| `tests/` | Offline unit and regression tests |
| `docs/history/` | Completed plans and progress records |
| `archive/` | Retired experimental implementations |

## Content and licensing

The MIT license covers original code and documentation only. The book-derived corpus
and any business-context fixtures are not relicensed. Review
[DATA_AND_CONTENT_NOTICE.md](DATA_AND_CONTENT_NOTICE.md) before redistributing this
repository.

## Remaining work

The implementation and narrative evidence pass the automated gate. The remaining
portfolio-completion item is a final manual visual review of the rendered local HTML;
see [OPEN_ITEMS.md](OPEN_ITEMS.md).
