# Current Query Generation Experiment

**Date:** 2026-08-10
**Status:** Development leader identified; holdout validation remains open

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
focus terms, subjects, and relevance labels are hidden. Every method produces one query,
uses no subject filter, and is scored through the same local hybrid retrieval path over
the same 30 exposed development cases.

## Audited results

| Method | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw user question | 63.3% | 86.7% | 90.0% | 1.444 |
| Unguided model rewrite | 60.0% | 93.3% | 96.7% | 1.517 |
| Corpus-guided model rewrite | **90.0%** | **96.7%** | **100.0%** | **1.200** |

Before these numbers were finalized, the returned passages were checked for both
missing valid labels and incorrectly permissive labels. Corrections were applied to the
shared answer key and every saved method was rescored without regenerating queries or
rerunning retrieval. The complete review is recorded in
`evals/reports/query_generation_label_audit.md`.

## Decision

The corpus-guided rewrite is the development leader. Its advantage is largest at
Hit@1: it more often puts a directly useful passage first, reducing how much evidence
the agent must inspect. It is a holdout finalist, not yet the product default, because
the prompt and labels were developed on these exposed cases.

## Current evidence files

- `evals/reports/query_generation_current.md` — canonical current result
- `evals/reports/query_generation_label_audit.md` — relevance-label review
- `evals/advisor_search_query_cases_enriched_labels.jsonl` — shared audited labels
- `evals/reports/query_generation_methods_dev_cases.jsonl` — preserved raw and unguided case results
- `evals/reports/query_generation_guided_v2_dev_cases.jsonl` — preserved corpus-guided case results
- `evals/runs/query_generation/v1/` and `evals/runs/query_generation/v2/` — prompts, generations, and retrieval outputs

The older aggregate reports remain in the repository as historical run artifacts, but
they are not the source of truth for the current three-method comparison.
