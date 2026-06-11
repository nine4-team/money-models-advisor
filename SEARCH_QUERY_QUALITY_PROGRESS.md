# Search-Query Quality Progress

This tracker is for one problem only: when source-material search is the correct tool, whether the generated query retrieves useful Money Models chunks.

It is separate from next-action classification. Query quality should not be evaluated on turns where the agent should not have searched in the first place.

## Current Status

The local source-material search stack exists and is auditable:

- heading-aware transcript chunks
- five-layer taxonomy
- BM25-style local baseline
- OpenAI embedding-backed vector search with disk-cached embeddings
- hybrid search using reciprocal-rank fusion over BM25 and vector rankings
- `search_source_material` CLI command
- session logs with `retrieval_queries` and returned `evidence`

The 1584 Design trace showed repeated generic diagnostic queries after the snapshot became diagnosable, even when later turns needed a different source focus or no source search at all. That exposed two separate problems: the agent must select the right source need, and the query builder must turn that source need into a compact corpus query.

Current search-query slice: `evals/advisor_search_query_cases.jsonl` now contains 30 search-appropriate turns, and `scripts/eval_search_query_quality.py` can score reviewer-authored reference queries, deterministic source-need-generated queries, or generated variants plus fallback.

- Plain generated BM25: `evals/reports/retrieval_backend_comparison.md` shows 93.3% known-useful Hit@3 and 100.0% Hit@5.
- Plain generated vector/hybrid each miss `searchq_v1_001` at Hit@5.
- Generated variants + hybrid: `evals/reports/retrieval_backend_comparison_generated_variants.md` shows 100.0% known-useful Hit@3/Hit@5, mean known-useful rank 1.17, and no top-5 misses.
- Operational reporting now shows latency, query count, variant count, vector-search count, corpus/query embedding cache behavior, and estimated embedding cost. On the warm-cache generated-variants run, hybrid used 4.0 queries per case, 120 vector searches across 30 cases, 100.0% query/corpus cache hit rates, and zero external embedding API batches.

Treat these as query-development baselines with non-exhaustive known-useful chunk labels, not as production IR benchmarks. The important finding is that the query builder works when the advisor-selected source need is explicit; the next risk is source-need selection by the acting agent.

After the source-need generation eval reached the seed gate, retrieval-backend comparison became the next valid experiment. `scripts/compare_retrieval_backends.py` now runs BM25, vector, and hybrid retrieval against the same generated-query cases and writes `evals/reports/retrieval_backend_comparison.md`. Vectorization may use the OpenAI embeddings API, but only for embedding text. The agent work remains outside the API path, and embeddings are cached under `.cache/embeddings/` for cost savings and repeatability.

Current backend comparison on generated queries:

| Backend | Known-useful Hit@3 | Known-useful Hit@5 | Mean known-useful rank | Misses @5 |
|---|---:|---:|---:|---|
| BM25 | 93.3% | 100.0% | 1.43 | none |
| Vector | 96.7% | 96.7% | 1.34 | `searchq_v1_001` |
| Hybrid | 96.7% | 96.7% | 1.21 | `searchq_v1_001` |

Decision: keep BM25 as the lexical baseline/control, not the product architecture. Plain vector and hybrid still expose one real top-5 weakness on `searchq_v1_001`, but generated query variants plus fusion fix that miss and make hybrid+variants the strongest candidate on the expanded 30-case slice. The operational report makes the tradeoff visible: variants improve quality but multiply query/vector-search work. Because the slice is still portfolio-scale, do not claim final production superiority yet; use hybrid+variants as the candidate product path while continuing golden-set expansion and production adapter work.

Miss adjudication:

- `searchq_v1_010` was a label-set limitation, not a true vector failure. Vector ranked `attraction-offers:0` first, and that chunk directly defines attraction offers as free/discount front-end offers that generate leads and customers. The known-useful labels now include it.
- Several expansion misses were also label-set limitations, not true retrieval failures. Retrieved `menu-upsell`, `rollover-upsell`, `waived-fee`, and `continuity-bonus` chunks were directly citeable and were added to the known-useful labels after inspection.
- `searchq_v1_001` remains a true vector/hybrid weakness at top 5. The user asks why fulfillment cost matters for whether ads can work. BM25 retrieves the clean CAC/GP/payback framework chunk at rank 1 and a payback-definition chunk at rank 4. Vector and hybrid mostly retrieve adjacent payback, CAC, CFA, and upsell-timing chunks; `gross-profit:0`, the clearest fulfillment-cost/gross-profit explanation, appears only at rank 8. This suggests dense retrieval is semantically close but less citation-ready for exact framework explanations.
- Generated query variants fix `searchq_v1_001` for hybrid by separating the gross-profit/fulfillment-cost meaning from the broader CAC/payback wording. With variants and fusion, hybrid retrieves `gross-profit:0` at rank 1.

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
6. After query construction is sane, compare BM25, vector, and hybrid retrieval on the same cases.

The target is not exact-query matching. The target is source material that can support the advisor's answer with citations.

First prove that the agent can decide when to search and generate source-specific search requests. Then retrieval-model comparisons become meaningful.

## Done Criteria

For the first v1 pass:

- 30 search-appropriate turns labeled **Done**
- each has expected purpose, layer, and focus terms **Done**
- generated queries do not reuse the generic diagnostic query unless the current turn actually calls for it **Done when `SourceNeed` is supplied**
- top retrieved chunks are useful enough to cite for most cases **Done on the expanded 30-case known-useful labels**
- BM25 remains the baseline/control; vector/hybrid comparison waits until the query set is stable **Done for first expanded comparison; hybrid+variants is the candidate product path**

## Next Work

Pinecone parity is complete for the 30-case generated-variants slice. The corpus was indexed as 202 heading-aware chunk vectors. `--vector-store pinecone` preserves the local quality direction: hybrid+variants reaches 100.0% Hit@3, 100.0% Hit@5, mean known-useful rank 1.17, and no top-5 misses. Cached embeddings kept the comparison at zero external embedding API batches. The remaining retrieval-engineering question is hosted-vector latency: the current sequential variant harness performs 120 Pinecone vector searches and shows roughly 5.3s p50 retrieval latency for hybrid, so the next optimization is reducing or parallelizing query fanout without losing quality.
