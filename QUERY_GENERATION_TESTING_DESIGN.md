# Query Generation Testing Design

**Date:** 2026-08-11
**Status:** Corpus-guided method selected across the 46-case audited regression suite.

## Goal

Figure out a reliable way to generate search queries that retrieve Money Models
passages which help answer the user's actual question.

The three methods below are not the goal. They are a small set of reasonable approaches
used to investigate the goal without assuming a complicated query system in advance.

## Product Boundary

This experiment begins only after the agent has decided that source-material search is
appropriate:

```text
current user question + saved BusinessSnapshot facts
-> query-generation method
-> one search query
-> CLI retrieval
-> ranked source passages
```

It does not test whether the agent should search, prior-session relevance, multi-query
fanout, metadata filtering, namespaces, reranking, or final-answer composition. Those
mechanisms should be tested separately only when a measured failure creates a reason.

## Dataset

The regression suite contains 46 realistic, search-worthy user turns across multiple
business scenarios. Each case includes:

- the user turn
- the accepted saved business snapshot available at that point
- the retrieval purpose
- non-exhaustive passage-level relevance labels
- challenge tags and provenance needed for analysis

Reference queries, reviewer focus terms, expected subjects, and relevance labels are
never shown to the query generator.

The suite began with 30 development cases and later gained 16 cases from four new
scenarios. All 46 are now exposed and reviewed, so current reports treat them as one
regression suite rather than claiming an unopened holdout.

## Methods Under Test

### Raw user question

Use the current question unchanged.

This is the simplest control. It tests whether generation adds enough retrieval quality
to justify its latency and complexity.

### Unguided model rewrite

Give the model the current question and the normal generator-visible business snapshot.
Ask it for one concise source-search query.

This tests whether ordinary language cleanup and contextualization are sufficient
without a corpus-specific dependency.

### Corpus-guided model rewrite

Give the same model the same question and snapshot plus a compact, reviewed guide to
the corpus vocabulary and frameworks. The guide is a translation reference, not a
checklist: the query must preserve every concept required by the user's mechanism,
relationship, comparison, or sequence while excluding concepts added only because they
are nearby in the guide.

This tests whether corpus vocabulary and framework relationships help the model retrieve
the right evidence when the user does not already speak in the book's terminology.

## Controlled Execution

All three methods are evaluated with:

- the same 46 cases and shared relevance labels
- exactly one query per case
- no subject or namespace filter
- the real CLI retrieval path
- an explicit retrieval backend
- top five returned passages
- saved prompts, generated queries, raw responses, CLI outputs, and case-level scores

Both model methods use the same `gpt-5.5` Codex harness and the same visible snapshot
projection. Only the corpus-guided condition receives the corpus guide. The raw control
receives no snapshot because its design is to use the user's question unchanged.

Hybrid retrieval is the product-candidate backend used for the main method comparison.
BM25 is retained as a lexical control.

## Scoring

The primary metrics are:

- **Hit@1:** a directly useful passage is ranked first
- **Hit@3:** a directly useful passage appears in the first three results
- **Hit@5:** a directly useful passage appears in the first five results
- **Mean first useful rank:** how much evidence the agent must inspect before finding
  useful support, calculated among top-five hits
- **Precision@5:** the mean percentage of each case's five returned passages that is
  directly useful
- **Noise@5:** the remaining percentage of top-five passages, calculated as
  `100% - Precision@5`

The reports also retain generation validity, latency, token proxies, retrieval latency,
missed cases, useful-passage counts per case, and complete case-level rankings.

## Relevance-Label Quality Check

Before finalizing the scores, the retrieved passages were checked in both
directions:

- For false negatives, unlabeled passages above the first labeled result and every
  top-five passage for a miss were reviewed.
- For false positives, every labeled case-passage pair returned in the top five by any
  current method was reviewed.

A passage is relevant only when it directly supports a substantial part of the requested
explanation, comparison, mechanism, or recommendation. Topic overlap alone is not enough.
Every correction is applied to the shared labels and every saved method is rescored.
The initial adjudication is recorded in `evals/reports/query_generation_label_audit.md`;
the completed approach × model × retriever pool is recorded in
`evals/reports/query_generation_full_matrix_audit.md`.

## Audited 46-Case Result

| Query approach | Model | Retriever | Hit@1 | Hit@3 | Hit@5 | Useful@5 | Noise@5 |
|---|---|---|---:|---:|---:|---:|---:|
| Raw question | none | BM25 | 54.3% | 69.6% | 84.8% | 40.0% | 60.0% |
| Raw question | none | Hybrid | 65.2% | 82.6% | 84.8% | 44.3% | 55.7% |
| Unguided | `gpt-5.5` | BM25 | 60.9% | 87.0% | 93.5% | 50.0% | 50.0% |
| Unguided | `gpt-5.5` | Hybrid | 67.4% | 93.5% | 95.7% | 54.3% | 45.7% |
| Unguided | `gpt-5.4-mini` | BM25 | 56.5% | 80.4% | 89.1% | 50.4% | 49.6% |
| Unguided | `gpt-5.4-mini` | Hybrid | 67.4% | 91.3% | 95.7% | 55.2% | 44.8% |
| Corpus-guided | `gpt-5.5` | BM25 | 84.8% | 93.5% | 97.8% | **74.3%** | **25.7%** |
| Corpus-guided | `gpt-5.5` | Hybrid | **93.5%** | 97.8% | **100.0%** | 71.7% | 28.3% |
| Corpus-guided | `gpt-5.4-mini` | BM25 | 84.8% | 95.7% | **100.0%** | 71.7% | 28.3% |
| Corpus-guided | `gpt-5.4-mini` | Hybrid | 89.1% | **100.0%** | **100.0%** | 71.7% | 28.3% |

All generated queries were valid. The corpus-guided method leads at every reported
coverage metric under hybrid and remains the strongest approach under BM25. It reduces
top-five hybrid noise by 17.4 points relative to the unguided `gpt-5.5` rewrite.

## Current Decision

The corpus-guided rewrite is now the selected runtime: the operating
agent uses the versioned corpus guide to write one query, and the CLI executes it
without a subject/namespace filter through hybrid retrieval. The prior multi-query
fallback path remains available only for historical eval reproducibility and manual
debugging.

## Model Selection Still Open

After fixing the corpus-guided method, the same prompt and guide were run with
`gpt-5.4-mini`, the smaller model already used elsewhere in the project. Across 46
cases, Mini scored 89.1%/100.0%/100.0% Hit@1/Hit@3/Hit@5 versus
`gpt-5.5` at 93.5%/97.8%/100.0%. Both returned 165 useful passages in 230 slots:
71.7% Useful@5 and 28.3% Noise@5. Mini was slower and used more Codex-reported tokens
in this harness, although those token counts are not API billing.

These retrieval metrics do not settle the runtime model because the answering agent
receives all five passages. Keep the existing `gpt-5.5` runtime unchanged while the
choice remains open. The next experiment should hold the answering model fixed, give
it each model's frozen top-five evidence, and score required-claim support, citation
correctness, unsupported claims, and answer usefulness. Precision@5 measures noise,
not whether the useful passages cover distinct required claims.

The unguided rewrite was also run with Mini to check for a model-by-approach
interaction. Across all 46 cases, unguided Mini scored 67.4%/91.3%/95.7%
Hit@1/Hit@3/Hit@5 with 55.2% Useful@5, while guided Mini scored
89.1%/100.0%/100.0% with 71.7% Useful@5. Corpus guidance therefore improves both
tested models and both retrievers.

Multi-query generation or filtering should be introduced only if a specific remaining
failure justifies a separate experiment.

## Current Evidence

- `evals/reports/query_generation_current.md` — canonical current result
- `evals/reports/query_generation_full_matrix_summary.json` — machine-readable matrix
- `evals/reports/query_generation_full_matrix_audit.md` — completed pooled-label review
- `evals/reports/query_generation_label_audit.md` — false-negative and false-positive review
- `evals/advisor_search_query_cases_enriched_labels.jsonl` — audited shared labels
- `evals/query_generation/query_generation_holdout_v1.jsonl` — 16-case expansion slice with audited shared labels
- `evals/reports/query_generation_holdout_v1.md` — preserved expansion-slice comparison
- `evals/reports/query_generation_holdout_v1_label_audit.md` — false-negative and false-positive review
- `evals/reports/query_generation_model_comparison.md` — query-generation model selection
- `evals/reports/retrieval_backend_query_writer_comparison.md` — paired BM25/hybrid comparison under both query writers
- `evals/reports/retrieval_backend_relevance_audit.md` — label audit triggered by the backend comparison
- `evals/runs/query_generation/` — preserved prompts, model outputs, and retrieval responses

Superseded development analysis is retained under
`evals/query_generation/archive/` for provenance, but it is not referenced by the
current narrative or used as the current result.
