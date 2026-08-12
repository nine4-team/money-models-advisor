# Current Query Generation Experiment

**Date:** 2026-08-11
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
retrieval, completing the approach × model × retriever matrix.

## Audited 46-case result

The suite began with 30 development cases and later gained 16 cases from four new
business scenarios. All are now known and reviewed, so the current decision treats
them as one regression suite.

| Query approach | Model | Retriever | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank | Useful@5 | Noise@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Raw question | none | BM25 | 54.3% | 69.6% | 84.8% | 1.821 | 40.4% | 59.6% |
| Raw question | none | Hybrid | 67.4% | 82.6% | 84.8% | 1.308 | 44.8% | 55.2% |
| Unguided rewrite | `gpt-5.5` | BM25 | 60.9% | 87.0% | 93.5% | 1.558 | 50.9% | 49.1% |
| Unguided rewrite | `gpt-5.5` | Hybrid | 67.4% | 93.5% | 95.7% | 1.409 | 57.0% | 43.0% |
| Unguided rewrite | `gpt-5.4-mini` | BM25 | 56.5% | 80.4% | 89.1% | 1.561 | 51.3% | 48.7% |
| Unguided rewrite | `gpt-5.4-mini` | Hybrid | 67.4% | 91.3% | 95.7% | 1.432 | 55.7% | 44.3% |
| Corpus-guided rewrite | `gpt-5.5` | BM25 | 84.8% | 93.5% | 97.8% | 1.289 | **75.2%** | **24.8%** |
| Corpus-guided rewrite | `gpt-5.5` | Hybrid | **93.5%** | 97.8% | **100.0%** | 1.130 | 73.0% | 27.0% |
| Corpus-guided rewrite | `gpt-5.4-mini` | BM25 | 84.8% | 95.7% | **100.0%** | 1.326 | 72.2% | 27.8% |
| Corpus-guided rewrite | `gpt-5.4-mini` | Hybrid | 89.1% | **100.0%** | **100.0%** | **1.109** | 72.6% | 27.4% |

## False-negative and false-positive check

Across all recorded retrieval audits, we added 150 missing useful case-passage
labels and removed 13 overly broad labels, for 163 corrections in total.

Every query and retrieval result was frozen before the relevance audits. Missing valid
passages and incorrectly permissive labels were corrected in the shared answer key,
then every saved result was rescored without regeneration or retrieval. The successive
reviews are recorded in `evals/reports/query_generation_label_audit.md`,
`query_generation_holdout_v1_label_audit.md`, and
`retrieval_backend_relevance_audit.md`, followed by the completed-matrix review in
`query_generation_full_matrix_audit.md`. Codex performed the semantic review rather
than an independent human adjudicator.

Corpus guidance wins under both retrievers and both tested models, so the approach
decision is not an artifact of one model or backend. Hybrid improves the raw and
unguided conditions on both coverage and evidence density. With the guided winner,
hybrid ranks useful evidence earlier and preserves 100% Hit@5, while BM25 is slightly
denser for the `gpt-5.5` query set. `gpt-5.5` puts useful evidence first more often;
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
- `evals/reports/query_generation_full_matrix_summary.json` — machine-readable combined result
- `evals/reports/query_generation_full_matrix_audit.md` — completed pooled-label audit
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
