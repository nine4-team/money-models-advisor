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

- **Model routing and tiering.** Partially done, corrected: `scripts/eval_codex_model_routing.py` now runs the source-need and tool-use golden suites through the actual Codex CLI agent harness and records the result in `evals/reports/model_routing_tiering.md`. Result: `gpt-5.5` via Codex CLI is close to the recorded acting-agent baseline but not perfect (85.7% strict source-need pass, 95.8% strict tool-use pass), and no cheaper Codex tier is promoted because `gpt-5-mini` is not supported in this ChatGPT subscription harness.
- **Multi-provider tradeoff evidence.** Still open for a controlled same-harness comparison. The prior OpenAI API replay is now treated as a separate provider/API experiment, not the product-routing decision, because it did not let models operate the CLI.
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
| "Own and improve RAG pipelines across multiple Pinecone namespaces" | The active 46-case suite compared one namespace with five oracle-routed subject namespaces. Both reached 93.5% Hit@1, 100% Hit@5, and 78.7% Useful@5; the split did not improve quality. | No reason to ship semantic namespace routing on this corpus. | Keep one unfiltered namespace and rerun only if corpus scale creates measurable interference. |
| "Chunking strategy" | Five strategies were screened on 32 chapter-labeled cases and revalidated on the 46-case passage-labeled hybrid path. Framework-aware is selected. | Strong enough for portfolio. | Keep as-is unless new retrieval failures point to chunking. |
| "Embedding model selection" | Small and Large were compared on 46 frozen queries at 1,536 dimensions. Large preserved 100% Hit@5 and improved Useful@5 from 78.7% to 86.5%; it is the runtime default. | Broader golden coverage remains useful. | Preserve the comparison as a regression and add genuinely new cases. |
| "Hybrid retrieval" | The full query/model matrix compares BM25 and hybrid. The selected one-query hybrid path preserves 100% Hit@5 and improves Useful@5 over BM25 under both guided query writers. | Strong enough, with portfolio-scale caveat. | Keep expanding the golden set and preserve BM25 as control. |
| "Reranking" | Reciprocal-rank fusion combines BM25 and vector rankings in the selected hybrid path. No separate learned reranker is adopted. | A learned reranker has no measured need on the current suite. | Revisit when useful passages enter the candidate pool but regularly miss the top five. |
| "Golden datasets" | `GOLDEN_DATASET.md` maps multiple JSONL suites and reports. | Strong. | Keep expanding breadth and preserve the Codex-harness model-routing run as a regression suite. |
| "Automated quality scoring" | Scorers cover tool use, current source events, query quality, retrieval, calculations, and a six-answer semantic audit with hash-bound judgments. | Answer-quality breadth is still small. | Expand the answer audit with new business contexts and observed failures. |
| "Retrieval metrics" | Hit@k, MRR, rank, support coverage, latency/cost tables. | Good. | Keep current caveats around non-exhaustive relevance labels. |
| "Latency benchmarks" | The active Pinecone replay records p50/p95 and exposed a 10x vector over-fetch; removing it preserved rankings and the selected Large path now measures 1.13s p50 / 1.43s p95. | Whole-turn latency remains model-harness dependent. | Keep hosted retrieval latency as a regression and use metered end-to-end timing when deployed. |
| "Regression detection" | Golden suites, run artifacts, reports, trace validators. | No CI gate yet. | Add a single command or CI workflow that runs the stable subset and fails on regressions. |
| "Optimize model routing and tiering to improve unit economics while maintaining output quality" | `scripts/eval_codex_model_routing.py` runs source-need and tool-use suites through `codex exec`, so the model can use the local CLI and write normal trace artifacts. The report records quality, latency, Codex-reported token usage, and failure modes for `gpt-5.5`. | The proper harness currently exposes only `gpt-5.5`; an attempted `gpt-5-mini` Codex run failed as unsupported for this ChatGPT account. This means the corrected result is a baseline, not a completed cheap-tier promotion. | Add a supported cheaper Codex profile/model when available, or run a separately labeled API/provider experiment only for bounded non-agent subtasks. Gate any downgrade on matching the Codex-harness baseline. |
| "Instrument the AI layer for observability: cost-per-request, token usage, quality signals, anomaly detection" | Retrieval reports record cache hits, estimated embedding cost, latency, and quality. Session traces record actions and sources. | No unified AI observability report; agent token/cost is missing or only available as proxy. No anomaly detection. | Add `evals/reports/ai_observability.md` summarizing cost/request, token or token-proxy usage, quality metrics, cache hit rate, latency, and anomaly flags. |
| "7+ years shipping production software systems: distributed backends, APIs, deployment pipelines, monitoring" | Tests and clean abstractions exist, but product is CLI-first. | Weak if presented as production software. | Add thin API/deployment/monitoring skeleton only after AI eval story is solid; do not overclaim. |
| "Production RAG systems using vector databases: Pinecone, Qdrant, FAISS, or Weaviate" | Pinecone adapter, index command, vector-store boundary, parity eval. | Need clearer index management and namespace story. | Add index-management docs/report: index name, namespace, embedding model, dimension, upsert count, cache behavior, and parity run. |
| "AI agents or multi-step LLM workflows in production: tool use, orchestration, system integrations" | Agent-operated CLI and subagent/acting-agent eval traces. | Not production; system integrations are local. | Claim multi-step workflow design and evaluation, not production deployment. Add model-tier tests because agents are the core product behavior. |
| "Evaluation framework for an LLM-based product: retrieval quality measurement, regression detection, model-switching decisions based on data" | Strong for retrieval and regression; model-switching now has a data-backed decision in `evals/reports/model_routing_tiering.md`. | CI gate for the stable golden subset still missing. | Add a single command or CI workflow that runs the stable suites and fails on regressions. |
| "Reduced LLM API costs through model routing, caching, token management, or architecture" | Cached embeddings and snapshot cache reduce repeated work; the Codex-harness routing eval records token-proxy usage and latency for agent planning; deterministic CLI work remains the primary cost-reduction architecture. | No cheaper Codex tier has been validated, so model routing is not yet a cost win. | Keep the routing report as the baseline; add a cheaper supported Codex profile/model only when it can run the same CLI-backed suite. |
| "Multiple LLM providers and tradeoffs" | Five OpenAI and Anthropic models ran the same 24 tool-use cases three times each; the narrative reports strict pass by run and treats cross-provider latency/token values as harness proxies. | Billed cost is not comparable across subscription harnesses. | Add billed cost only when models run through a metered deployment path. |
| "TypeScript and Python" | Python core is strong. | TypeScript is absent from the active product. | Add a minimal TypeScript API/client or web surface over the Python CLI/core. Keep it thin and avoid reimplementing advisor logic. |

## Recommended Priority Order

Completed: model routing, query generation, chunking, embedding selection, BM25-versus-hybrid comparison, Pinecone namespace and latency tests, calculation verification, and a seed semantic answer audit.

Remaining, in order:

1. **Golden breadth.** Add genuinely new business contexts and observed failures.
2. **CI/deployment/monitoring skeleton.** Run the stable golden subset as an explicit gate.
3. **Thin TypeScript/API/web surface.** Add only if it strengthens the final submission
   without duplicating advisor logic.
4. **Comparable billed cost.** Record it when the deployment path exposes metered
   model calls.

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

The model-routing result should feature prominently in the narrative, but with the corrected claim: the project now has a proper Codex/CLI baseline for OpenAI agent execution, and it refuses to promote cheaper routing from an API harness that does not match the product. That restraint is the senior signal.
