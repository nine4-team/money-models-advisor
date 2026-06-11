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
- Retrieval decisions are data-backed: heading-aware chunking remains the default; BM25 is the lexical baseline/control; hybrid retrieval with constrained query variants is the candidate product path after vector/hybrid comparison.
- Embeddings are cached under `.cache/embeddings/` so repeated vector runs reuse corpus and query vectors.
- The narrative records decisions, metrics, misses, and non-adoptions rather than treating every sophisticated technique as automatically better.

Weak alignment / gaps to close:

- The golden dataset is now explicit in `GOLDEN_DATASET.md`; the next gap is breadth, not structure.
- The current vector backend is local/in-memory with cached OpenAI embeddings. The JD explicitly mentions production RAG systems using vector databases such as Pinecone, Qdrant, FAISS, or Weaviate. The project should either add a lightweight vector-index adapter or clearly document the production adapter boundary.
- Query generation v2 is implemented as constrained `SourceNeed.query_variants` with the deterministic flattened query retained as a fallback/control.
- Observability is present through traces and reports, but cost/token/latency reporting should become more explicit.

## Next JD-Aligned Work

The next highest-signal work is:

1. Expand the golden dataset breadth enough to support the hybrid+variants candidate story without overclaiming production finality.
2. Expand the golden search-query set before claiming hybrid+variants as final.
3. Add latency, embedding-cache, and cost-oriented reporting to the retrieval comparisons.
4. Record latency and embedding-cache behavior in the backend comparison report.
5. Decide whether to add a lightweight vector database adapter or document the adapter boundary as planned production work.

This keeps the work aligned with the JD: golden datasets first, measured retrieval improvements second, production-oriented infrastructure third.
