# Evaluation Reports

This directory contains the reports that support the current architecture and
portfolio narrative. Superseded, exploratory, incomplete, and rejected experiments
are under `archive/`.

## Current report index

| Product question | Canonical report |
|---|---|
| Which query approach, query writer, and retriever should we use? | `active_framework_retrieval_matrix.md` |
| Does the selected query approach survive infrastructure changes? | `query_generation_current.md` |
| Which chunking strategy should we use? | `active_query_chunking_revalidation.md` |
| Which embedding setup should we use? | `embedding_model_comparison.md` |
| Does one namespace or subject partitioning work better on Pinecone? | `active_query_pinecone_revalidation.md` |
| What Pinecone candidate depth is sufficient? | `pinecone_candidate_depth_optimization.md` |
| Does the selected embedding preserve quality on Pinecone? | `pinecone_large_embedding_revalidation.md` |
| How well do the tested models decide whether search is needed? | `search_decision_model_comparison.md` |
| Does the agent choose the correct next action? | `advisor_tool_use_judgment.md` |
| Are search events valid and auditable? | `advisor_source_event_traces.md` |
| Are calculation events recomputable? | `advisor_calculation_trace_events.md` |
| Are full answers useful and supported? | `advisor_answer_quality_expanded.md` |

Machine-readable summaries and case-level files sit beside the relevant Markdown
report. `GOLDEN_DATASET.md` maps each report to its cases, risk, scorer, and current
decision.

## Stable offline gate

```bash
python3 scripts/regression_gate.py
```

The gate scores saved artifacts. It does not regenerate acting-agent runs or call an
embedding API or hosted vector store.

## Retrieval revalidation

```bash
python3 scripts/revalidate_retrieval_choices.py chunking
python3 scripts/revalidate_retrieval_choices.py matrix
```

The matrix holds the 46 cases and saved queries fixed while comparing the raw
question, unguided rewrite, and corpus-guided rewrite through BM25 and hybrid
retrieval. The chunking command replays all five strategies on the selected guided
query path.

## Agent behavior and answer quality

```bash
python3 scripts/eval_tool_use_judgment.py --require-all-pass
python3 scripts/eval_source_event_traces.py --require-all-pass
python3 scripts/eval_calculation_trace_events.py
python3 scripts/eval_advisor_answer_quality.py --require-all-pass
```

The semantic relevance and answer-quality audits were performed by Codex rather than
an independent human reviewer. The reports disclose that limitation where it affects
interpretation.
