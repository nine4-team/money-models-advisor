# JD Requirements Audit

This audit maps the verbatim Acquisition.com Senior AI Engineer job description in `JOB_DESCRIPTION.md` to the current project evidence, the real gaps, and the highest-signal work still worth doing.

The point is not to build everything in the JD. The point is to make the portfolio project show senior AI engineering judgment: prove the parts we can prove, name the parts we are intentionally not claiming, and avoid mistaking a local demo for production experience.

## Summary

The project is strongest on:

- golden datasets and regression-oriented evaluation
- agent/tool boundaries
- local CLI orchestration and trace capture
- retrieval experiments over BM25, vector, hybrid, query variants, and Pinecone-backed storage
- cached embeddings and retrieval cost observability

The biggest easy JD-aligned gaps are:

1. **Model routing and tiering.** We have golden suites, but we have not run the same cases across multiple model/provider tiers or produced a routing decision.
2. **Multi-provider tradeoff evidence.** The docs should show observed prompt-following, trace reliability, latency/cost, and failure-mode differences across provider/model families where available.
3. **Embedding strategy selection.** We have cached OpenAI embeddings and Pinecone, but the narrative should compare embedding models, quality, latency, and cost before calling one the default.
4. **Pinecone index and namespace management.** We have a Pinecone adapter and parity run, but should explicitly demonstrate namespace/index operations, not just query a hosted vector store.
5. **Reranking.** The JD names reranking. We should either test a reranker or explicitly record why fusion is the v1 reranking substitute and what would trigger a true reranker.
6. **Observability across the AI layer.** Retrieval reports have latency/cache/cost metrics, but the product needs a consolidated observability report: cost per request, token or token-proxy usage, quality signals, and anomaly flags.
7. **Production software surface.** The current product is CLI-backed. To show APIs, TypeScript, deployment shape, and user-facing product readiness, the next surface should be a thin TypeScript API/web layer over the same Python core, not a second implementation.

## Detailed Mapping

| JD language | Current evidence | Gap | Best next proof |
|---|---|---|---|
| "Design, build, and deploy production-grade AI agents and end-to-end agentic workflows" | Agent-operated CLI, skill guidance, `session start`, `session finish`, source events, calculation events, product-smoke traces. | Not deployed; production-grade claim would be too strong. | Keep claiming "production-oriented architecture." Add API/deployment skeleton only after model-routing and observability evidence. |
| "Solve real business problems across ACQ Vantage" | Advisor solves a real business-model diagnosis/use-case; 1584 product-smoke sessions exercise realistic business context. | Domain is not ACQ Vantage. | Frame as analogous business-advisor workflow, not as ACQ-specific production use. |
| "Integrate LLMs with internal systems, APIs, and data sources" | Agent uses CLI tools, saved `BusinessSnapshot`, local business docs, Money Models corpus, Pinecone. | No external business API integration; local-doc inspection is not the same as API/data-system integration. | Add a thin service/API contract and a mock business-system adapter, or explicitly defer. Do not hard-code 1584 file structure. |
| "Reliability, performance, and clean abstractions" | Tests, eval reports, trace validation, vector-store boundary, cached embeddings, latency tables. | No end-to-end service SLO or monitoring threshold yet. | Add observability report with pass/fail thresholds and anomaly flags. |
| "Collaborate with product and engineering teams to prioritize, ship, and iterate quickly" | Iterative test-fix loop and product-smoke reports show prioritization. | Hard to prove in code. | Narrative should emphasize measured iteration and scoped decisions, not pretend team collaboration happened. |
| "Own and improve RAG pipelines across multiple Pinecone namespaces" | Pinecone vector store supports namespace parameters, local namespace simulation, and mechanical layer-to-physical namespace mapping. The five Money Models layer namespaces are indexed in Pinecone: `money-models-unit-economics`, `money-models-offers`, `money-models-upsells`, `money-models-downsells`, and `money-models-continuity`. Local 30-case oracle testing shows unchanged hybrid quality versus single namespace. A hosted 5-case Pinecone namespace smoke preserves hybrid quality at 100.0% Hit@3/Hit@5. | Namespace support is demonstrated, but the full hosted namespace benchmark is not production-latency-ready because the current harness executes query-variant x namespace fanout sequentially. Also, oracle namespace labels are not the same as proving the agent picks namespaces correctly. | Keep single namespace plus metadata filtering as the simpler v1 default unless namespace selection shows a quality/latency win. Next proof: add a separate agent namespace-selection eval and parallel/bounded hosted retrieval before full Pinecone namespace latency claims. |
| "Chunking strategy" | Heading-aware vs framework-aware chunking comparison exists; heading-aware kept by decision rule. | Strong enough for portfolio. | Keep as-is unless new retrieval failures point to chunking. |
| "Embedding model selection" | OpenAI embedding client supports model-specific cache; reports include cache namespace. | We have not compared embedding models as a selection experiment. | Run `text-embedding-3-small` vs `text-embedding-3-large` on the same query-variant eval and record quality/latency/cost. |
| "Hybrid retrieval" | BM25, vector, and hybrid are compared; hybrid+variants is candidate default. | Strong enough, with portfolio-scale caveat. | Keep expanding golden set and preserve BM25 as control. |
| "Reranking" | Reciprocal-rank fusion promotes chunks repeated across variants; no true reranker tested. | JD explicitly names reranking, so this is under-covered. | Add a small reranking experiment or record that RRF is the v1 rank-fusion baseline and a cross-encoder/LLM reranker is deferred pending measured need. |
| "Golden datasets" | `GOLDEN_DATASET.md` maps multiple JSONL suites and reports. | Strong. | Add model-routing/tiering matrix over existing suites. |
| "Automated quality scoring" | Scorers for tool use, source need, source events, query quality, retrieval, calculations. | Answer-quality scoring is less mature. | Add agent/human-adjudicated answer-quality rubric for product-smoke outputs. |
| "Retrieval metrics" | Hit@k, MRR, rank, support coverage, latency/cost tables. | Good. | Keep current caveats around non-exhaustive relevance labels. |
| "Latency benchmarks" | Retrieval backend reports include p50/p95 total/retrieval/embedding. | Mostly retrieval-only, not whole advisor turn. | Add end-to-end turn latency or trace-duration fields where available. |
| "Regression detection" | Golden suites, run artifacts, reports, trace validators. | No CI gate yet. | Add a single command or CI workflow that runs the stable subset and fails on regressions. |
| "Optimize model routing and tiering to improve unit economics while maintaining output quality" | Not yet proven. Existing golden suites make it easy to test. | Major gap. | Run identical agent/eval tasks across model tiers, record pass rate/cost/latency/failure modes, and write a routing policy. |
| "Instrument the AI layer for observability: cost-per-request, token usage, quality signals, anomaly detection" | Retrieval reports record cache hits, estimated embedding cost, latency, and quality. Session traces record actions and sources. | No unified AI observability report; agent token/cost is missing or only available as proxy. No anomaly detection. | Add `evals/reports/ai_observability.md` summarizing cost/request, token or token-proxy usage, quality metrics, cache hit rate, latency, and anomaly flags. |
| "7+ years shipping production software systems: distributed backends, APIs, deployment pipelines, monitoring" | Tests and clean abstractions exist, but product is CLI-first. | Weak if presented as production software. | Add thin API/deployment/monitoring skeleton only after AI eval story is solid; do not overclaim. |
| "Production RAG systems using vector databases: Pinecone, Qdrant, FAISS, or Weaviate" | Pinecone adapter, index command, vector-store boundary, parity eval. | Need clearer index management and namespace story. | Add index-management docs/report: index name, namespace, embedding model, dimension, upsert count, cache behavior, and parity run. |
| "AI agents or multi-step LLM workflows in production: tool use, orchestration, system integrations" | Agent-operated CLI and subagent/acting-agent eval traces. | Not production; system integrations are local. | Claim multi-step workflow design and evaluation, not production deployment. Add model-tier tests because agents are the core product behavior. |
| "Evaluation framework for an LLM-based product: retrieval quality measurement, regression detection, model-switching decisions based on data" | Strong for retrieval and regression; missing model-switching. | Major gap. | Model-routing/tiering matrix is the direct fix. |
| "Reduced LLM API costs through model routing, caching, token management, or architecture" | Cached embeddings and snapshot cache reduce repeated work. | Missing LLM reasoning cost reduction through routing/tiering. | Add routing policy and cost comparison. Add prompt/context budget notes for snapshot use. |
| "Multiple LLM providers and tradeoffs" | Not yet documented with results. | Major gap if ignored. | Run or record comparable model/provider traces with prompt behavior, failure modes, latency, and cost/cost proxy. |
| "TypeScript and Python" | Python core is strong. | TypeScript is absent from the active product. | Add a minimal TypeScript API/client or web surface over the Python CLI/core. Keep it thin and avoid reimplementing advisor logic. |

## Recommended Priority Order

1. **Model-routing and tiering eval.** Highest signal because it reuses existing golden suites and maps directly to multiple JD lines.
2. **Multi-provider/model-family comparison.** Pair with the routing eval where possible so this is not a separate science project.
3. **Embedding model selection.** Run `text-embedding-3-small` vs `text-embedding-3-large` over the existing retrieval suite and report quality/cost/latency.
4. **AI observability report.** Consolidate quality, latency, cache, token/cost, and anomaly signals into one report.
5. **Pinecone namespace/index-management evidence.** Show hosted vector operations beyond "query worked once," including a small multi-namespace experiment because the JD explicitly names multiple Pinecone namespaces.
6. **Reranking decision.** Test a reranker or explicitly justify RRF as the v1 rank-fusion baseline.
7. **Thin TypeScript/API/web surface.** Build only after the model-routing and observability story is stronger, so the frontend/API work showcases the same core rather than distracting from it.
8. **CI/deployment/monitoring skeleton.** Useful, but lower priority than AI-specific requirements unless the final submission needs stronger production-software optics.

## What Not To Do

- Do not create new schema just to satisfy one business-specific example.
- Do not build a large web app before the AI behavior and routing story is credible.
- Do not claim production deployment when the artifact is a local portfolio system.
- Do not treat BM25 as the final product architecture; keep it as the lexical baseline/control.
- Do not use external model APIs for hidden answer synthesis unless the experiment is explicitly about model/provider comparison and the results are recorded.

## Next Concrete Work

Create a model-routing/tiering report over existing cases:

- Inputs: existing tool-use, source-need, source-event/query-variant, and product-smoke cases.
- Candidate tiers: at least one stronger model and one cheaper/faster model; include multiple providers if available.
- Outputs: `evals/reports/model_routing_tiering.md`, plus machine-readable summary JSON/JSONL if the run harness supports it.
- Decision: task-by-task routing recommendation, including which tasks stay deterministic in the CLI.

This should become the next prominent result in the narrative because it directly answers the JD's model-routing, model-switching, unit-economics, and provider-tradeoff requirements.
