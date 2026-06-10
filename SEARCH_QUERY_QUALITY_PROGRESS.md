# Search-Query Quality Progress

This tracker is for one problem only: when source-material search is the correct tool, whether the generated query retrieves useful Money Models chunks.

It is separate from next-action classification. Query quality should not be evaluated on turns where the agent should not have searched in the first place.

## Current Status

The local source-material search stack exists and is auditable:

- heading-aware transcript chunks
- five-layer taxonomy
- BM25-style local baseline
- `search_source_material` CLI command
- session logs with `retrieval_queries` and returned `evidence`

The current weakness is query construction. The 1584 Design trace showed repeated generic diagnostic queries after the snapshot became diagnosable, even when later turns needed a different source focus or no source search at all.

First seed baseline: `evals/advisor_search_query_cases.jsonl` now contains 10 search-appropriate turns, and `scripts/eval_search_query_quality.py` generates `evals/reports/advisor_search_query_quality.md`. The current seed report shows 100.0% known-useful Hit@3/Hit@5 and 100.0% top-1 layer match. Treat this as a query-development baseline with non-exhaustive known-useful chunk labels, not as a production IR benchmark.

## Known Failure Modes

| Failure | Example | Why it matters |
|---|---|---|
| Over-broad query | CAC + payback + business type + ICP + core offer | Dilutes the actual source need |
| Stale query reuse | Same diagnostic query across later turns | Ignores the current user turn |
| Wrong source focus | Ad-spend question gets generic payback query | Retrieves plausible but incomplete support |
| Missing concept query | "Why do we need fulfillment cost?" gets no source search | The answer may be uncited or weakly grounded |
| Business context stuffing | Long business descriptions in every query | Can crowd out framework terms |

## Evaluation Strategy

Only include turns where source-material search is the expected action.

Each row should include:

- conversation context summary
- current user turn
- expected retrieval purpose: concept teaching, diagnostic explanation, comparison, or recommendation support
- expected corpus layer
- expected focus terms
- generated query
- returned chunks
- reviewer judgment of returned chunk usefulness

Primary metric:

- useful source material in top 3 or top 5

Secondary diagnostics:

- query focus: does the query match the user turn's source need?
- layer correctness: did it search the right corpus layer?
- chunk specificity: are returned chunks directly citeable, not merely adjacent?
- redundancy: does the same query repeat across different source needs?

## Improvement Loop

1. Start from search-appropriate turns only.
2. Label expected retrieval purpose, layer, and focus terms.
3. Generate compact source-seeking queries from the current turn plus minimal snapshot context.
4. Inspect top chunks.
5. Revise query examples/templates when chunks are broad, stale, or irrelevant.
6. After query construction is sane, compare BM25, dense, and hybrid retrieval on the same cases.

The target is not exact-query matching. The target is source material that can support the advisor's answer with citations.

## Done Criteria

For the first v1 pass:

- at least 10 search-appropriate turns labeled **Done**
- each has expected purpose, layer, and focus terms **Done**
- generated queries do not reuse the generic diagnostic query unless the current turn actually calls for it **Done in seed cases; not yet enforced in runtime query generation**
- top retrieved chunks are useful enough to cite for most cases **Done on seed known-useful labels**
- BM25 remains the baseline; dense/hybrid comparison waits until the query set is stable **Still active**

## Next Work

Update `src/money_model_architect/advisor_queries.py` so generated queries are driven by the current advisor-selected source need, not snapshot status alone.
