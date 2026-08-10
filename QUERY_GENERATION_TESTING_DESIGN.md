# Query Generation Testing Design

**Date:** 2026-08-10
**Status:** Development leader identified; independent holdout validation remains open.

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

The development set contains 30 realistic, search-worthy user turns. Each case includes:

- the user turn
- the accepted saved business snapshot available at that point
- the retrieval purpose
- non-exhaustive passage-level relevance labels
- challenge tags and provenance needed for analysis

Reference queries, reviewer focus terms, expected subjects, and relevance labels are
never shown to the query generator.

The current 30 cases are exposed development and regression data. A separate 16-case,
multi-scenario holdout has been authored but remains unopened until its passage labels
receive independent human review.

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

- the same 30 cases and shared relevance labels
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

The reports also retain generation validity, latency, token proxies, retrieval latency,
missed cases, and complete case-level rankings.

## Relevance-Label Quality Check

Before finalizing the development scores, the retrieved passages were checked in both
directions:

- For false negatives, unlabeled passages above the first labeled result and every
  top-five passage for a miss were reviewed.
- For false positives, every labeled case-passage pair returned in the top five by any
  current method was reviewed.

A passage is relevant only when it directly supports a substantial part of the requested
explanation, comparison, mechanism, or recommendation. Topic overlap alone is not enough.
Every correction is applied to the shared labels and every saved method is rescored.
The full adjudication is recorded in
`evals/reports/query_generation_label_audit.md`.

## Audited Development Result

| Method · hybrid retrieval | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw user question | 63.3% | 86.7% | 90.0% | 1.444 |
| Unguided model rewrite | 60.0% | 93.3% | 96.7% | 1.517 |
| Corpus-guided model rewrite | **90.0%** | **96.7%** | **100.0%** | **1.200** |

All generated queries were valid. The corpus-guided method is the clear development
leader, especially at Hit@1. The raw question slightly exceeds the unguided rewrite at
Hit@1, while the unguided rewrite retrieves useful evidence more often by ranks three
and five. This suggests that generic rewriting alone improves breadth but not first-rank
precision.

## Current Decision

The corpus-guided rewrite is the holdout finalist. It is not yet the product default
because its prompt and relevance labels were developed against the exposed cases.

Before adoption:

1. Independently review and freeze the 16 holdout cases and passage labels.
2. Freeze the current three methods, prompts, guide, model, and repeat count.
3. Run the holdout once through the same CLI and hybrid retrieval path.
4. Compare quality, latency, and failure modes.
5. Promote the simplest method that preserves the required retrieval quality.

Model-tier comparison follows method selection; it does not replace it. Multi-query
generation or filtering should be introduced only if a specific remaining failure
justifies a separate experiment.

## Current Evidence

- `evals/reports/query_generation_current.md` — canonical current result
- `evals/reports/query_generation_label_audit.md` — false-negative and false-positive review
- `evals/advisor_search_query_cases_enriched_labels.jsonl` — audited shared labels
- `evals/query_generation/query_generation_holdout_v1.jsonl` — unopened candidate holdout
- `evals/runs/query_generation/` — preserved prompts, model outputs, and retrieval responses

Superseded development analysis is retained under
`evals/query_generation/archive/` for provenance, but it is not referenced by the
current narrative or used as the current result.
