# Target Job Description

This project is being built as a portfolio artifact for the Acquisition.com Senior AI Engineer role.

Source:

- Original posting: https://jobs.ashbyhq.com/acquisition/9789dd49-c6bd-4672-8cd3-9f67f2dea7c1
- Verbatim posting text below, pulled from the Ashby posting API on 2026-06-11. The Role Summary section further down is an earlier paraphrase; where wording matters (e.g. mapping deliverables to JD phrases), use the verbatim text.
- Requirement-by-requirement project audit: `JD_REQUIREMENTS_AUDIT.md`

## Verbatim Posting (Ashby, 2026-06-11)

### Role

The Senior AI Engineer builds and deploys production-grade AI agents that power ACQ Vantage. This role exists to turn AI capability into real, usable systems that drive business outcomes, not experiments or prototypes.

You will work inside a lean Technology team to design, build, and ship agentic workflows that interact with internal tools, data systems, and user-facing products. You are responsible for taking ideas from concept to production, with a focus on reliability, speed, and practical value.

This is a hands-on engineering role. You are writing code daily, iterating quickly, and working directly with modern AI tooling. You are expected to understand how LLMs behave in production, not just how they work in theory.

### Responsibilities

- Design, build, and deploy production-grade AI agents and end-to-end agentic workflows that solve real business problems across ACQ Vantage
- Integrate LLMs with internal systems, APIs, and data sources, ensuring reliability, performance, and clean abstractions
- Collaborate with product and engineering teams to prioritize, ship, and iterate on AI features quickly
- Own and improve RAG pipelines across multiple Pinecone namespaces, including chunking strategy, embedding model selection, hybrid retrieval, and reranking
- Build and maintain an evaluation framework, including golden datasets, automated quality scoring, retrieval metrics, latency benchmarks, and regression detection
- Optimize model routing and tiering to improve unit economics while maintaining output quality
- Instrument the AI layer for observability, including cost-per-request, token usage, quality signals, and anomaly detection

### Requirements

- 7+ years shipping production software systems (distributed backends, APIs, deployment pipelines, monitoring)
- 2+ years building production RAG systems using vector databases (Pinecone, Qdrant, FAISS, or Weaviate), including embedding strategies, index management, and retrieval tuning
- Built and deployed AI agents or multi-step LLM workflows in production, including tool use, orchestration, and system integrations
- Built or contributed to an evaluation framework for an LLM-based product (retrieval quality measurement, regression detection, model-switching decisions based on data)
- Reduced LLM API costs in production through model routing, caching, token management, or architectural improvements
- Worked across multiple LLM providers (OpenAI, Anthropic, or equivalent) and understands tradeoffs in prompt behavior, token economics, and failure modes
- Comfortable in both TypeScript and Python (our stack uses both)

### Results

- Production AI agents are deployed and actively used within ACQ Vantage
- New AI-driven features move from concept to production in weeks, not months
- Agent performance improves over time through structured testing and iteration
- AI systems operate reliably with minimal failure or manual intervention
- Engineering output translates directly into measurable business impact

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
- The biggest remaining JD gap is model routing and tiering. The project has golden datasets and trace scorers, but it has not yet run the same agent tasks across multiple model/provider tiers to decide which tasks can use cheaper/faster models without losing output quality.
- Multi-provider tradeoff evidence is also missing. The narrative should not merely say "understands OpenAI and Anthropic"; it should show comparable runs, observed failure modes, latency/cost notes, and a routing decision.

## Next JD-Aligned Work

The next highest-signal work is:

1. Run model-routing and tiering evals over the existing golden suites: tool-use judgment, source-need generation, source-event/query-variant traces, and product-smoke turns. Compare at least a strong model tier and a cheaper/faster model tier, and record pass rate, failure modes, latency, and cost or cost proxy.
2. Convert those results into a routing decision: which tasks require the strongest model, which can safely use a cheaper tier, and which should stay deterministic inside the CLI.
3. Add multi-provider comparison evidence where available, especially prompt-following behavior, trace completeness, source-need quality, token economics, and failure modes.
4. Optimize hosted-vector latency by reducing or parallelizing query-variant fanout while preserving hybrid+variants quality.
5. Continue expanding the golden dataset breadth enough to support the hybrid+variants candidate story without overclaiming production finality.
6. Keep Pinecone quality/latency/cache/cost reports beside local vector-store reports as the hosted retrieval guardrail.

This keeps the work aligned with the JD: model routing must be data-backed, retrieval choices must be measured, and production-oriented infrastructure should support the eval story rather than distract from it.
