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
- The project has explicit eval assets for next-action classification, search
  decisions, source-event logging, query quality, chunking, retrieval, and answer
  support.
- Retrieval decisions are data-backed: framework-aware chunking is the default;
  BM25 is the lexical control; one corpus-guided, unfiltered query through hybrid
  retrieval is the selected path after the full 46-case comparison.
- Embeddings are cached under `.cache/embeddings/` so repeated vector runs reuse corpus and query vectors.
- The narrative records decisions, metrics, misses, and non-adoptions rather than treating every sophisticated technique as automatically better.

Additional current evidence:

- The golden dataset is explicit in `GOLDEN_DATASET.md`. Full-answer coverage now
  includes 20 balanced cases across five business contexts; the expanded suite
  exposed and drove a general input-sufficiency correction before passing 20/20.
- The vector backend has local and Pinecone implementations. The selected Large,
  1,536-dimension vectors are indexed in an isolated Pinecone namespace and replayed
  on the active 46-case one-query suite.
- Query generation is implemented as one `SearchRequest.query` written by the operating agent from the current question, saved snapshot, and the same versioned corpus guide used by the winning experiment. The CLI applies no request-time filter and defaults that structured request to hybrid; the old variants/fallback path is compatibility-only.
- Observability is now present through traces, Markdown reports, summary JSON, case-level JSONL, latency metrics, cache hit/miss accounting, and estimated embedding cost. Token/cost reporting is explicit for embeddings; agent work remains outside the API path.
- Model-routing evidence compares `gpt-5.5` and `gpt-5.4-mini` on 48 balanced
  search-decision cases. `gpt-5.5` scored 48/48 and remains the operating agent;
  Mini scored 47/48 and remains a tested bounded query-writer option.

## Next JD-Aligned Work

The next highest-signal work is:

1. Complete the final rendered narrative review against the canonical reports.
2. Add genuinely new cases when production-like use reveals new failure modes.
3. Add comparable billed model cost only when the deployment path exposes metered
   calls; do not treat cross-harness token proxies as billed cost.

This keeps the work aligned with the JD: model routing must be data-backed, retrieval choices must be measured, and production-oriented infrastructure should support the eval story rather than distract from it.
