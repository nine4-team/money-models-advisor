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

Gaps closed since the first pass of this audit:

- **Model routing and tiering.** Done: `scripts/eval_model_routing.py` replays the source-need and tool-use golden suites across 4 OpenAI tiers and records a routing decision in `evals/reports/model_routing_tiering.md`. Result: no tested downgrade maintains planning quality, so nothing routes downward in v1.
- **Multi-provider tradeoff evidence.** Partially done inside the same report: tier and family failure-mode differences are measured (reasoning tiers fail closed, the non-reasoning tier fails open and breaks output format), with the recorded Claude interactive traces as a cross-provider reference. A controlled same-harness cross-provider run still requires an Anthropic API key.
- **Pinecone index and namespace management.** Done: five-layer namespace indexing, single vs oracle-namespace benchmarks, and the recorded decision to keep single namespace plus metadata filtering (DESIGN.md).
- **Reranking.** Done as a recorded decision: RRF over query variants is the v1 reranking baseline; a cross-encoder is gated on evidence that ordering, not recall, is the failure (DESIGN.md).

The remaining JD-aligned gaps are:

1. **Embedding strategy selection.** We have cached OpenAI embeddings and Pinecone, but the narrative should compare embedding models, quality, latency, and cost before calling one the default. Caveat: the current 30-case slice is saturated at Hit@5, so this comparison needs either a harder slice or an explicit "no measurable difference" framing.
2. **Observability across the AI layer.** Retrieval reports have latency/cache/cost metrics, but the product needs a consolidated observability report: cost per request, token or token-proxy usage, quality signals, and anomaly flags.
3. **Production software surface.** The current product is CLI-backed. To show APIs, TypeScript, deployment shape, and user-facing product readiness, the next surface should be a thin TypeScript API/web layer over the same Python core, not a second implementation.

## Detailed Mapping

| JD language | Current evidence | Gap | Best next proof |
|---|---|---|---|
| "Design, build, and deploy production-grade AI agents and end-to-end agentic workflows" | Agent-operated CLI, skill guidance, `session start`, `session finish`, source events, calculation events, product-smoke traces. | Not deployed; production-grade claim would be too strong. | Keep claiming "production-oriented architecture." Add API/deployment skeleton only after model-routing and observability evidence. |
| "Solve real business problems across ACQ Vantage" | Advisor solves a real business-model diagnosis/use-case; 1584 product-smoke sessions exercise realistic business context. | Domain is not ACQ Vantage. | Frame as analogous business-advisor workflow, not as ACQ-specific production use. |
| "Integrate LLMs with internal systems, APIs, and data sources" | Agent uses CLI tools, saved `BusinessSnapshot`, local business docs, Money Models corpus, Pinecone. | No external business API integration; local-doc inspection is not the same as API/data-system integration. | Add a thin service/API contract and a mock business-system adapter, or explicitly defer. Do not hard-code 1584 file structure. |
| "Reliability, performance, and clean abstractions" | Tests, eval reports, trace validation, vector-store boundary, cached embeddings, latency tables. | No end-to-end service SLO or monitoring threshold yet. | Add observability report with pass/fail thresholds and anomaly flags. |
| "Collaborate with product and engineering teams to prioritize, ship, and iterate quickly" | Iterative test-fix loop and product-smoke reports show prioritization. | Hard to prove in code. | Narrative should emphasize measured iteration and scoped decisions, not pretend team collaboration happened. |
| "Own and improve RAG pipelines across multiple Pinecone namespaces" | Pinecone vector store supports namespace parameters, local namespace simulation, and mechanical layer-to-physical namespace mapping. The five Money Models layer namespaces are indexed in Pinecone: `money-models-unit-economics`, `money-models-offers`, `money-models-upsells`, `money-models-downsells`, and `money-models-continuity`. Full 30-case hosted Pinecone benchmarks now complete for both single/default namespace and five-layer oracle namespace conditions with bounded parallel retrieval. Both preserve hybrid quality at 100.0% Hit@3/Hit@5 and mean rank 1.17. | Oracle namespace labels are not the same as proving the agent picks namespaces correctly. The namespace condition also adds hosted vector searches, 140 vs 120, and worsens p95 hybrid retrieval, about 3.01s vs 1.76s. | Keep single namespace plus metadata filtering as the v1 default. The agent namespace-selection eval is intentionally dropped: per-case comparison showed identical rankings even with oracle routing, so namespace selection has no quality to win and only latency to lose. |
| "Chunking strategy" | Heading-aware vs framework-aware chunking comparison exists; heading-aware kept by decision rule. | Strong enough for portfolio. | Keep as-is unless new retrieval failures point to chunking. |
| "Embedding model selection" | OpenAI embedding client supports model-specific cache; reports include cache namespace. | We have not compared embedding models as a selection experiment. | Run `text-embedding-3-small` vs `text-embedding-3-large` on the same query-variant eval and record quality/latency/cost. |
| "Hybrid retrieval" | BM25, vector, and hybrid are compared; hybrid+variants is candidate default. | Strong enough, with portfolio-scale caveat. | Keep expanding golden set and preserve BM25 as control. |
| "Reranking" | Recorded decision in DESIGN.md: RRF over constrained query variants is the v1 reranking baseline. The current slice is saturated (100% Hit@5), so a true reranker cannot show a win on it. | Covered as an explicit decision rather than an experiment. | Revisit when a golden slice shows known-useful chunks in top-20 but not top-5 — that is the ordering failure a cross-encoder fixes. |
| "Golden datasets" | `GOLDEN_DATASET.md` maps multiple JSONL suites and reports. | Strong. | Add model-routing/tiering matrix over existing suites. |
| "Automated quality scoring" | Scorers for tool use, source need, source events, query quality, retrieval, calculations. | Answer-quality scoring is less mature. | Add agent/human-adjudicated answer-quality rubric for product-smoke outputs. |
| "Retrieval metrics" | Hit@k, MRR, rank, support coverage, latency/cost tables. | Good. | Keep current caveats around non-exhaustive relevance labels. |
| "Latency benchmarks" | Retrieval backend reports include p50/p95 total/retrieval/embedding. | Mostly retrieval-only, not whole advisor turn. | Add end-to-end turn latency or trace-duration fields where available. |
| "Regression detection" | Golden suites, run artifacts, reports, trace validators. | No CI gate yet. | Add a single command or CI workflow that runs the stable subset and fails on regressions. |
| "Optimize model routing and tiering to improve unit economics while maintaining output quality" | `scripts/eval_model_routing.py` replays source-need and tool-use suites across `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, and `gpt-4.1-mini` with pass rate, latency, token, cost, and failure-mode tables plus a written routing policy in `evals/reports/model_routing_tiering.md`. | The measured answer is that no downgrade maintains quality on planning tasks, so the unit-economics lever stays deterministic CLI work, not model swaps. | Re-run when a bounded low-stakes subtask (e.g. query-variant phrasing) becomes a downgrade candidate; gate any downgrade on matching the recorded baseline. |
| "Instrument the AI layer for observability: cost-per-request, token usage, quality signals, anomaly detection" | Retrieval reports record cache hits, estimated embedding cost, latency, and quality. Session traces record actions and sources. | No unified AI observability report; agent token/cost is missing or only available as proxy. No anomaly detection. | Add `evals/reports/ai_observability.md` summarizing cost/request, token or token-proxy usage, quality metrics, cache hit rate, latency, and anomaly flags. |
| "7+ years shipping production software systems: distributed backends, APIs, deployment pipelines, monitoring" | Tests and clean abstractions exist, but product is CLI-first. | Weak if presented as production software. | Add thin API/deployment/monitoring skeleton only after AI eval story is solid; do not overclaim. |
| "Production RAG systems using vector databases: Pinecone, Qdrant, FAISS, or Weaviate" | Pinecone adapter, index command, vector-store boundary, parity eval. | Need clearer index management and namespace story. | Add index-management docs/report: index name, namespace, embedding model, dimension, upsert count, cache behavior, and parity run. |
| "AI agents or multi-step LLM workflows in production: tool use, orchestration, system integrations" | Agent-operated CLI and subagent/acting-agent eval traces. | Not production; system integrations are local. | Claim multi-step workflow design and evaluation, not production deployment. Add model-tier tests because agents are the core product behavior. |
| "Evaluation framework for an LLM-based product: retrieval quality measurement, regression detection, model-switching decisions based on data" | Strong for retrieval and regression; model-switching now has a data-backed decision in `evals/reports/model_routing_tiering.md`. | CI gate for the stable golden subset still missing. | Add a single command or CI workflow that runs the stable suites and fails on regressions. |
| "Reduced LLM API costs through model routing, caching, token management, or architecture" | Cached embeddings and snapshot cache reduce repeated work; the routing eval records measured per-case cost across tiers and the decision that deterministic CLI work, not model downgrades, is the cost lever. | Honest framing: routing did not reduce cost here because no cheaper tier held quality; the architecture (deterministic CLI) is the cost reduction. | Keep the routing report as the cost-decision artifact; add prompt/context budget notes for snapshot use. |
| "Multiple LLM providers and tradeoffs" | `evals/reports/model_routing_tiering.md` records tier and family tradeoffs: reasoning tiers fail closed, the non-reasoning tier fails open and violates the output contract, latency/cost differ ~10-20x. Recorded Claude interactive traces serve as a cross-provider reference with the harness difference stated. | A controlled same-harness cross-provider run needs an Anthropic API key. | Add the Anthropic condition to `eval_model_routing.py` when a key is available; the adapter only needs a second endpoint. |
| "TypeScript and Python" | Python core is strong. | TypeScript is absent from the active product. | Add a minimal TypeScript API/client or web surface over the Python CLI/core. Keep it thin and avoid reimplementing advisor logic. |

## Recommended Priority Order

Completed: model-routing/tiering eval (`evals/reports/model_routing_tiering.md`), tier/family tradeoff evidence (same report), Pinecone namespace experiment (DESIGN.md decision record), and the reranking decision (DESIGN.md). The agent namespace-selection eval previously suggested as a namespace follow-up is intentionally dropped: namespaces showed no retrieval benefit even with oracle routing, so scoring agent namespace selection would evaluate a capability the product has no reason to ship.

Remaining, in order:

1. **AI observability report.** Consolidate quality, latency, cache, token/cost, and anomaly signals into one report. The routing eval added real token/cost/latency instrumentation that this report can consume.
2. **Embedding model selection.** Run `text-embedding-3-small` vs `text-embedding-3-large` over the existing retrieval suite and report quality/cost/latency. Decide up front how to frame a likely "no measurable difference" result, because the current slice is saturated at Hit@5.
3. **Thin TypeScript/API/web surface.** Build only after the observability story is stronger, so the frontend/API work showcases the same core rather than distracting from it. This is the only item covering the JD's TypeScript line.
4. **CI/deployment/monitoring skeleton.** Start with a single command that runs the stable golden subset and fails on regressions; expand only if the final submission needs stronger production-software optics.
5. **Anthropic API condition for the routing eval.** When a key is available, add the second provider endpoint to `eval_model_routing.py` for a controlled same-harness cross-provider comparison.

## What Not To Do

- Do not create new schema just to satisfy one business-specific example.
- Do not build a large web app before the AI behavior and routing story is credible.
- Do not claim production deployment when the artifact is a local portfolio system.
- Do not treat BM25 as the final product architecture; keep it as the lexical baseline/control.
- Do not use external model APIs for hidden answer synthesis unless the experiment is explicitly about model/provider comparison and the results are recorded.

## Next Concrete Work

Create the consolidated AI observability report:

- Inputs: retrieval backend summary JSONs (latency, cache hits, embedding cost), model-routing summary JSON (per-tier tokens, cost, latency, failure modes), and session trace artifacts.
- Outputs: `evals/reports/ai_observability.md` with cost per request, token or token-proxy usage, quality signals, cache hit rates, latency percentiles, and anomaly flags with explicit pass/fail thresholds.
- Decision: which signals gate promotion of retrieval or model changes, and what counts as an anomaly worth alerting on.

The model-routing result should feature prominently in the narrative: it directly answers the JD's model-routing, model-switching, unit-economics, and provider-tradeoff requirements with a measured "no downgrade holds quality" decision, which is a stronger senior signal than a cherry-picked cost win.
