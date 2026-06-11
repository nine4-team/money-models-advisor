# Target Job Description

This project is being built as a portfolio artifact for the Acquisition.com Senior AI Engineer role.

Source:

- Original posting: https://jobs.ashbyhq.com/acquisition/9789dd49-c6bd-4672-8cd3-9f67f2dea7c1
- Search-accessible mirror used for the current summary: LinkedIn listing for Acquisition.com Senior AI Engineer

## Role Summary

The role is a hands-on senior AI engineering role focused on building production-grade AI agents for ACQ Vantage. The job description emphasizes practical systems that drive business outcomes, not isolated demos or prototypes.

Core responsibilities and requirements include:

- design, build, and deploy production-grade AI agents and end-to-end agentic workflows
- integrate LLMs with internal tools, APIs, data systems, and user-facing products
- own and improve RAG pipelines, including chunking strategy, embedding model selection, hybrid retrieval, and reranking
- build and maintain evaluation frameworks with golden datasets, automated quality scoring, retrieval metrics, latency benchmarks, and regression detection
- optimize model routing and tiering to improve unit economics while maintaining quality
- instrument the AI layer for observability, including cost per request, token usage, quality signals, and anomaly detection
- reduce LLM API costs with model routing, caching, token management, or architectural improvements
- understand tradeoffs across multiple LLM providers
- work comfortably in Python and TypeScript

## Project North Star

The project should demonstrate senior-level AI engineering judgment for this JD. The goal is not to build the largest possible demo. The goal is to show that we can:

1. Build an agent-operated product loop with clear tool boundaries.
2. Use retrieval and source grounding in a measurable way.
3. Build and use golden datasets to drive architecture decisions.
4. Compare retrieval strategies with explicit metrics and failure analysis.
5. Cache embeddings and business context to control cost.
6. Record traces and reports that support regression detection.
7. Explain why each architectural choice was adopted, rejected, or deferred.

## Current Fit

Strong alignment:

- The advisor is agent-operated and CLI-backed: the agent plans; deterministic tools persist state, calculate, search, and record traces.
- The project has explicit eval assets for next-action classification, source-need generation, source-event logging, query quality, chunking, and retrieval backend comparison.
- Retrieval decisions are data-backed: heading-aware chunking remains the default; BM25 is the lexical baseline/control; hybrid retrieval with constrained query variants is the candidate product path after a 30-case golden search-query comparison.
- Embeddings are cached under `.cache/embeddings/` so repeated vector runs reuse corpus and query vectors.
- The narrative records decisions, metrics, misses, and non-adoptions rather than treating every sophisticated technique as automatically better.

Weak alignment / gaps to close:

- The golden dataset is now explicit in `GOLDEN_DATASET.md`; the next gap is breadth, not structure.
- The vector backend now has a storage boundary with local and Pinecone implementations. The local backend remains the fast eval baseline; the Pinecone path is indexed and parity-tested on the 30-case generated-variants slice.
- Query generation v2 is implemented as constrained `SourceNeed.query_variants` with the deterministic flattened query retained as a fallback/control.
- Observability is now present through traces, Markdown reports, summary JSON, case-level JSONL, latency metrics, cache hit/miss accounting, and estimated embedding cost. Token/cost reporting is explicit for embeddings; agent work remains outside the API path.

## Next JD-Aligned Work

The next highest-signal work is:

1. Optimize hosted-vector latency by reducing or parallelizing query-variant fanout while preserving hybrid+variants quality.
2. Continue expanding the golden dataset breadth enough to support the hybrid+variants candidate story without overclaiming production finality.
3. Keep Pinecone quality/latency/cache/cost reports beside local vector-store reports as the hosted retrieval guardrail.

This keeps the work aligned with the JD: golden datasets first, measured retrieval improvements second, production-oriented infrastructure third.
