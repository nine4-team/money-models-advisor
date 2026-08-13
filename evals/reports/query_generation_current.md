# Current Query Generation Experiment

**Date:** 2026-08-12
**Status:** Corpus-guided method selected and active in the CLI

## Goal

Identify a reliable way to generate search queries that retrieve Money Models passages
which help answer the user's actual question.

## Current experiment

The experiment compares three reasonable starting approaches:

1. Use the raw user question.
2. Ask a model to rewrite the question using the normal saved business snapshot.
3. Ask the same model to rewrite it using the same snapshot plus a compact guide to the
   corpus vocabulary and frameworks.

Each method receives only the information appropriate to its design. Reference queries,
focus terms, subjects, and relevance labels are hidden. Every method produces one query
and uses no subject filter. Each saved query is scored unchanged through BM25 and hybrid
retrieval over the framework-aware chunks used by the product, completing the
approach × model × retriever matrix.

## Audited 46-case result

The suite began with 30 development cases and later gained 16 cases from four new
business scenarios. All are now known and reviewed, so the current decision treats
them as one regression suite.

| Query approach | Model | Retriever | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Raw question | none | BM25 | 56.5% | 76.1% | 87.0% | 1.800 | 41.7% | 58.3% |
| Raw question | none | Hybrid | 63.0% | 80.4% | 87.0% | 1.525 | 50.9% | 49.1% |
| Unguided rewrite | `gpt-5.5` | BM25 | 73.9% | 91.3% | 95.7% | 1.364 | 55.7% | 44.3% |
| Unguided rewrite | `gpt-5.5` | Hybrid | 80.4% | 91.3% | 93.5% | 1.233 | 62.6% | 37.4% |
| Unguided rewrite | `gpt-5.4-mini` | BM25 | 67.4% | 80.4% | 91.3% | 1.619 | 55.2% | 44.8% |
| Unguided rewrite | `gpt-5.4-mini` | Hybrid | 76.1% | 87.0% | 91.3% | 1.333 | 62.6% | 37.4% |
| Corpus-guided rewrite | `gpt-5.5` | BM25 | 89.1% | 95.7% | 95.7% | 1.091 | 76.1% | 23.9% |
| Corpus-guided rewrite | `gpt-5.5` | Hybrid | **93.5%** | 97.8% | **100.0%** | 1.152 | 78.7% | 21.3% |
| Corpus-guided rewrite | `gpt-5.4-mini` | BM25 | 89.1% | 95.7% | **100.0%** | 1.217 | 74.8% | 25.2% |
| Corpus-guided rewrite | `gpt-5.4-mini` | Hybrid | 91.3% | **100.0%** | **100.0%** | **1.109** | **80.4%** | **19.6%** |

## False-negative and false-positive check

Across all recorded retrieval audits, we added 161 missing useful case-passage
labels and removed 14 overly broad labels.

Every query and retrieval result was frozen before the relevance audits. Missing valid
passages and incorrectly permissive labels were corrected in the shared answer key,
then every saved result was rescored without regeneration or retrieval. The successive
reviews are recorded in `evals/reports/query_generation_label_audit.md`,
`query_generation_holdout_v1_label_audit.md`, and
`retrieval_backend_relevance_audit.md`, followed by the heading-aware completed-matrix
review in `query_generation_full_matrix_audit.md` and the active-boundary review in
`active_framework_retrieval_matrix.md`. Codex performed the semantic review rather
than an independent human adjudicator.

Corpus guidance wins under both retrievers and both tested models, so the approach
decision is not an artifact of one model or backend. With the guided winner, hybrid
preserves 100% Hit@5 and improves useful evidence density under both tested models.
`gpt-5.5` puts useful evidence first more often;
Mini reaches useful evidence within three results on every guided case. This still
does not establish a final-answer-quality difference because the advisor receives all
five passages.

## Decision

Use the corpus-guided rewrite in the CLI: one query, no subject filter, through hybrid
retrieval. It leads the combined 46-case suite. The raw question remains the
no-generation control, and the unguided rewrite remains the control for whether the
corpus guide earns its added dependency.

## Current evidence files

- `evals/reports/query_generation_current.md` — canonical current result
- `evals/reports/active_framework_retrieval_matrix.md` — current method and boundary audit
- `evals/reports/active_framework_retrieval_matrix_summary.json` — machine-readable current result
- `evals/reports/query_generation_full_matrix_audit.md` — historical heading-aware pooled-label audit
- `evals/reports/query_generation_label_audit.md` — relevance-label review
- `evals/reports/query_generation_holdout_v1.md` — preserved 16-case expansion-slice comparison
- `evals/reports/query_generation_holdout_v1_label_audit.md` — expansion-slice relevance review
- `evals/reports/query_generation_model_comparison.md` — `gpt-5.5` versus `gpt-5.4-mini`
- `evals/reports/retrieval_backend_query_writer_comparison.md` — paired backend interpretation across all query conditions
- `evals/reports/retrieval_backend_relevance_audit.md` — shared-label audit triggered by the backend comparison
- `evals/reports/query_generation_unguided_5_4_mini_dev.md` and `query_generation_unguided_5_4_mini_holdout.md` — Mini approach-robustness runs
- `evals/advisor_search_query_cases_enriched_labels.jsonl` — shared audited labels
- `evals/query_generation/query_generation_holdout_v1.jsonl` — 16-case expansion slice with audited shared labels
- `evals/reports/query_generation_methods_dev_cases.jsonl` — preserved raw and unguided case results
- `evals/reports/query_generation_guided_v2_dev_cases.jsonl` — preserved corpus-guided case results
- `evals/runs/query_generation/v1/` and `evals/runs/query_generation/v2/` — prompts, generations, and retrieval outputs
- `evals/runs/query_generation/holdout_v1/` — frozen expansion-slice artifacts; directory name retained for provenance

The older aggregate reports remain in the repository as historical run artifacts, but
they are not the source of truth for the current three-method comparison.
