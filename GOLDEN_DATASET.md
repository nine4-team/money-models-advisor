# Golden Dataset Suite

This project uses a golden-dataset suite to evaluate the Money Model Advisor as an agent-operated, CLI-backed RAG system. The suite is intentionally small enough for a portfolio project, but it is structured like a production eval loop: each case file targets a specific product risk, each scorer produces an auditable report, and design decisions are recorded from measured behavior rather than vibes.

The target job description calls for golden datasets, retrieval metrics, automated quality scoring, regression detection, cached embeddings, and cost-aware AI systems. This file is the map from that requirement to the project artifacts.

## Definition

A golden dataset is a versioned set of examples with expected behavior, labels, scoring logic, reports, and decision notes.

In this repo, golden data can include:

- realistic user turns;
- fixture snapshots and conversation context;
- expected agent actions;
- expected `SourceNeed` objects;
- expected source-event traces;
- known-useful source chunks;
- required-claim support labels;
- adjudication notes when labels are corrected.

The labels are not all the same kind of truth. Some are strict behavioral expectations, such as "do not search source material for this turn." Others are seed relevance labels, such as "this chunk is known useful," where the set is useful but not exhaustive. Reports should say which kind of label they are using.

## Current Suite

| Dataset | Product Risk Tested | Scorer / Report | Current Result | Current Decision |
|---|---|---|---|---|
| `evals/advisor_tool_use_cases.jsonl` | Can the acting agent choose the right next action before answering? | `scripts/eval_tool_use_judgment.py`; `evals/reports/advisor_tool_use_judgment.md` | 24 / 24 scored. 1.000 required-action recall, 100.0% full-sequence pass rate, 0.0% false search, 0.0% missed search, 100.0% trace completeness. | Use as the current tool-use judgment baseline for the captured case set. |
| `evals/advisor_source_need_cases.jsonl` | When source-material search is appropriate, can the acting agent generate the right retrieval objective? | `scripts/eval_source_need_generation.py`; `evals/reports/advisor_source_need_generation.md` | 14 / 14 scored. 100.0% search decision accuracy, 0.0% false search, 0.0% missed search, 90.0% layer exact match, 0.950 average layer recall, 0.750 average focus-term concept recall. `intent` is recorded as an annotation and no longer scored (it steers no retrieval). | Good enough for seed retrieval-backend comparisons, with the free-trial `offers` / `downsells` residual carried as a caveat. |
| `evals/advisor_source_event_cases.jsonl` | Do completed traces record the right source-material searches, including multi-search answers, no-search turns, and agent-written query variants? | `scripts/eval_source_event_traces.py`; `evals/reports/advisor_source_event_traces.md`; stricter variant pass in `evals/reports/advisor_source_event_query_variants.md` | Base pass: 6 / 6 scored, 100.0% case pass rate, 6 / 6 expected source events matched, 0 extra source-event warnings. Query-variant pass: 6 / 6 scored, 100.0% case pass rate with `--require-query-variants`. | Use as the regression guard for source-event logging, over-search restraint, and query-variant trace completeness. |
| `evals/advisor_calculation_trace_cases.jsonl` | When the acting agent uses deterministic math, does the completed trace preserve the metric, inputs, and output? | `scripts/eval_calculation_trace_events.py`; `evals/reports/advisor_calculation_trace_events.md` | 5 / 5 scored. 100.0% case pass rate, 0 failures after correcting evaluator labels for the CLI's one-month payback convention and floating-point tolerance. | Keep `calculation_events` required whenever `actions` includes `calculate`. |
| `evals/advisor_product_smoke_scenarios.jsonl` | Does the advisor behave like a useful product across realistic multi-turn sessions? | Acting-agent sessions plus review in `evals/reports/advisor_product_smoke_v1.md` | 3 scenarios run. Directionally useful behavior, with product gaps surfaced: terminology/modeling cleanup around a business-specific candidate attraction offer, a now-corrected stale payback fixture, and noisy recommendation retrieval for front-end/attraction-offer searches. | Use after component evals pass to find product-level failures such as generic advice, premature recommendations, over-search, weak citations, or missing state updates. Next fix: recommendation-retrieval inspection without adding business-specific schema. |
| Codex-harness model-routing baseline over existing golden suites | How well does an OpenAI Codex agent perform on source-need and tool-use judgment when it can operate the actual CLI, and can any supported cheaper tier be promoted? | `scripts/eval_codex_model_routing.py`; `evals/reports/model_routing_tiering.md`; summary JSON and per-case run artifacts under `evals/runs/model_routing_codex/` | Corrected full run: `gpt-5.5` via Codex CLI over 38 cases. Source-need: 85.7% strict pass, 92.9% search decision, 90.0% layer exact (`intent` recorded but not scored). Tool-use: 95.8% strict pass, 0 false search, 0 missed search, 0 execution errors. Codex reported ~400k tokens for source-need and ~1.25M for tool-use; these are subscription-harness token proxies, not API bills. | The API replay is no longer used as the product-routing result. `gpt-5.5` is the current OpenAI Codex baseline; no cheaper Codex tier is promoted because `gpt-5-mini` is not supported in this ChatGPT subscription harness. Future model-routing work must use the same CLI-backed harness or be explicitly labeled as a separate API/provider experiment. |
| Cross-provider replication of the model-routing suites with Claude Opus 4.8 as the acting agent | Does a second-provider frontier model hold the semantic-planning role on the same CLI-backed suites, and where do the two providers differ? | Same prep + scorers via `scripts/eval_codex_model_routing.py::run_prepare`; `evals/reports/model_routing_opus.md`; summary JSON and per-case artifacts under `evals/runs/model_routing_opus/` | Opus 4.8 over the same 38 cases, identical acting prompts, isolated context per case. Source-need: 85.7% strict pass, 92.9% search decision, 90.0% layer exact (`intent` recorded but not scored). Tool-use: 91.7% strict pass, 0.972 required recall, 4.2% false search, 0 missed search. Recorded reference reproduced exactly, confirming a shared baseline. Token/latency proxies captured in `opus_runtime_proxy.json` (Claude Code subagent-reported, not API billing). | The two models tie on source-need and gpt-5.5 leads tool-use by a single case, inside the noise floor for n=14/n=24 single-shot. Residual failures are genuine and small (Opus: over-search + missed calculate; gpt-5.5: missed diagnose). Both frontier tiers are good enough for planning; cheaper-tier comparison through this same harness remains the open work. |
| `evals/advisor_search_query_cases.jsonl` plus `evals/advisor_query_variants_v2.jsonl` | Given a selected `SourceNeed`, does query construction retrieve citeable Money Models chunks? | `scripts/eval_search_query_quality.py`; generated and generated-variant reports; backend summary JSON and case JSONL artifacts | 30 generated-query cases after expansion and miss adjudication. Plain BM25 reaches 93.3% Hit@3 and 100.0% Hit@5. Plain vector/hybrid each miss `searchq_v1_001` at Hit@5. With v2 query variants and fusion, hybrid reaches 100.0% Hit@3/Hit@5 with mean known-useful rank 1.17; BM25/vector variants also reach 100.0% Hit@5. Warm-cache variant runs show 100.0% corpus/query embedding cache hit rates and zero external embedding API batches. | Treat BM25 as the lexical baseline/control. Move hybrid + constrained variants to candidate default, with continued golden-set validation required before calling it final. |
| Single-query generation-method development comparison over `evals/advisor_search_query_cases_enriched_labels.jsonl`; candidate holdout in `evals/query_generation/query_generation_holdout_v1.jsonl` | Starting from the real user question and saved snapshot, do raw search, unguided model rewrite, or model rewrite with a combined corpus guide retrieve better evidence? | `scripts/eval_query_generation_methods.py`; `evals/reports/query_generation_methods_dev.md`; summary JSON, case JSONL, and per-generation artifacts under `evals/runs/query_generation/v1/` | All 90 development queries were valid and frozen before scoring. Complete BM25 Hit@5: raw 76.7%, unguided 90.0%, guided 93.3%. Complete hybrid Hit@5: raw 90.0%, unguided 96.7%. Guided hybrid is incomplete at 24/30 cases and 91.7% Hit@5 on that sequential subset, so it is not directly comparable. | Preserve as development evidence only. Review and freeze the 16 candidate holdout labels before running any method on the holdout; do not promote a generation method from the exposed 30-case results. |
| Pinecone namespace experiment | Does the existing five-layer Money Models taxonomy make sense as a hosted Pinecone namespace layout? | `scripts/compare_retrieval_backends.py`; `evals/reports/retrieval_backend_comparison_generated_variants_pinecone_single_namespace.md`; `evals/reports/retrieval_backend_comparison_generated_variants_pinecone_layer_namespaces_oracle.md`; local control reports for single/default and oracle namespace conditions | Full 30-case Pinecone single/default and five-layer oracle namespace benchmarks now complete with `--max-workers 8`. Both preserve hybrid quality at 100.0% Hit@3/Hit@5 and mean rank 1.17. The namespace condition adds vector searches, 140 versus 120, and worsens p95 hybrid retrieval, about 3.01s versus 1.76s. Warm-cache query embeddings keep both at zero embedding API batches. | Namespace support is real and JD-relevant, but single namespace plus metadata filters remains the better v1 default on this eval slice: both conditions returned identical top-5 rankings on all 90 per-case rows, and the split only worsens tail latency. The agent namespace-selection eval is intentionally dropped because even oracle routing showed no quality to win. |
| `evals/golden.jsonl` | Does the local retriever find expected source material for a broad pilot query set? | `scripts/eval_retrieval.py`; `evals/reports/local_retrieval_baseline.md` | BM25 heading-aware baseline: 81.25% Hit@1, 100.00% Hit@5, 0.8917 MRR. | Keep as the local retrieval smoke benchmark. |
| Chunking comparison data generated by `scripts/compare_chunking.py` | Which chunking strategy gives the best retrieval quality without unnecessary complexity? | `evals/reports/chunking_comparison.md` | `heading-aware`: 81.25% Hit@1, 100.00% Hit@5, 0.8917 MRR. `framework-aware`: same Hit@1 and +0.0041 MRR. | Keep `heading-aware`; the framework-aware gain does not clear the adoption rule. |
| `evals/obligations.jsonl` | Do retrieved chunks support the claims an answer must make? | `scripts/score_obligation_support.py`; `evals/reports/obligation_support_coverage.md` | 65 accepted labels. BM25 heading-aware support coverage is 87.69%. | Use required-claim support coverage as a retrieval-support guardrail, not as the only ranking metric. |
| `evals/realistic_queries.jsonl` | Are eval queries phrased like real users rather than source-keyword prompts? | `scripts/audit_query_realism.py`; `evals/reports/query_realism.md` | Query-realism audit exists to keep search tests from artificially inflating lexical retrieval. | Keep realism checks separate from source-search cases so user realism and retrieval relevance do not get conflated. |

## Evaluation Ladder

The suite is ordered to avoid drawing conclusions from the wrong layer of the system.

1. Tool-use judgment: should the agent search source material, inspect saved state, inspect local docs, calculate, clarify, update memory, read logs, or answer directly?
2. Source-need generation: if source-material search is appropriate, what source support does this answer need?
3. Search-query quality: once a `SourceNeed` exists, does the query retrieve useful chunks?
4. Retrieval backend comparison: with tool use and query construction stable enough, do BM25, vector, or hybrid retrieval perform better?
5. Model-routing and tiering: can cheaper/faster model tiers preserve quality on simpler agent tasks, and where does the system need the stronger model?
6. Support and answer quality: do cited chunks actually support the required claims in the answer?
7. Product-smoke sessions: across realistic multi-turn conversations, does the advisor ask, save, calculate, search, cite, and recommend in a way a user would trust?

This order matters because retrieval-backend comparisons are not meaningful when the agent searches on the wrong turns or sends bad queries. First prove the agent can decide when to search and generate source-specific search requests. Then compare retrieval models.

The model-routing layer matters for the JD because quality alone is not the production decision. A senior AI engineer should be able to say which model tier is good enough for which task, how much quality is lost or preserved, and what unit-economics benefit the routing policy creates.

The product-smoke layer is intentionally different from the component evals. It does not replace precise tests for tool use, source needs, query quality, or trace shape. It answers the user's practical question: "Would I be embarrassed to show this advisor as a product?" These sessions should surface product-level failures that component tests can miss, such as advice that is technically trace-valid but generic, overcautious, poorly sequenced, or unhelpful under pushback.

## Label Strength

Not every metric should be interpreted the same way.

- Tool-use cases and source-event cases are strict behavioral tests.
- Source-need labels are semantic expectations. Scoring is on the fields that drive retrieval (search decision, layers, focus terms), with alias tolerance on focus terms; `intent` is recorded but not scored, since the diagnostic-vs-recommendation distinction it once graded changes no retrieval.
- Known-useful chunks in search-query cases are seed relevance labels, not exhaustive relevance judgments.
- Required-claim labels are human or agent-adjudicated support labels for specific claims, not a complete map of every useful chunk in the corpus.
- Exact focus-term recall is a debugging signal. Concept coverage with rationale is the stronger semantic signal.

When a report depends on non-exhaustive labels, the conclusion should be framed as an engineering signal rather than a production-quality benchmark.

## Development Rules

Before changing advisor behavior, identify which product risk the change is supposed to improve and which golden dataset should catch regressions.

Use an acting-agent test-fix loop for product workflow hardening:

1. Run blind acting agents on realistic turns.
2. Inspect saved traces, not only final answers.
3. Classify failures as path plumbing, tool choice, source need, retrieval, trace shape, or answer quality.
4. Fix the right layer: skill, CLI affordance, trace schema, eval case, or narrative.
5. Rerun after the fix.
6. Promote repeated or high-risk failures into a golden regression case.

Example: if agents list `calculate` in a trace but do not preserve the metric inputs and output, treat that as a trace-shape failure. The fix should be a structured trace field such as `calculation_events`, followed by a regression check that calculation actions are auditable.

When adding a new case:

1. Put it in the smallest dataset that matches the risk being tested.
2. Keep realistic user language unless the case is explicitly a harness test.
3. Include fixture state rather than burying saved facts in prompt text.
4. Record expected behavior in machine-readable labels.
5. Run the scorer and update the report.
6. Record the design interpretation in `DESIGN.md` or the relevant progress doc.

Do not tune for one visible miss unless the fix is a general rule and counter-cases still pass.

## Latest Query-Variants Experiment

The latest JD-aligned experiment is query variants.

The current query builder flattens a `SourceNeed` into one deterministic query. That is a useful v1 baseline because it isolates retrieval execution from agent judgment. The remaining vector/hybrid miss shows the limitation: a flat noun list can obscure the causal relationship the user is asking about.

The v2 implementation now:

- lets the agent generate constrained query variants from the selected `SourceNeed`;
- keeps the deterministic flattened query as a fallback variant;
- fuses variant results with reciprocal-rank fusion instead of letting early variants crowd out the fallback;
- compares variant performance against `evals/advisor_search_query_cases.jsonl`;
- reports BM25, vector, and hybrid behavior in `evals/reports/retrieval_backend_comparison_generated_variants.md`.

The first result is useful but not an automatic production adoption. Query variants fixed the vector/hybrid top-5 miss on the expanded eval slice, but they add another agent-authored artifact that can be wrong.

BM25 is the lexical baseline/control, not the product architecture. It tells us whether fancier retrieval is actually earning its complexity. The target architecture is: agent generates structured `SourceNeed`; agent or planner generates constrained query variants; retrieval runs hybrid search over lexical + vector candidates; results are fused/reranked; embeddings are cached for cost control; golden datasets track quality regressions, latency, and cost.

The hiring narrative should say: "I started with BM25 as a baseline because exact framework terms are strong in this corpus. Then I tested vector and hybrid retrieval. Plain vector/hybrid underperformed on one diagnostic case, which exposed a query-generation weakness. I added constrained query variants plus fusion, expanded the golden search-query slice from 10 to 30 cases, adjudicated newly retrieved citeable chunks, and found that hybrid+variants was strongest on the expanded slice. Because the dataset is still portfolio-scale, I would not overclaim final production superiority, but the production-facing architecture is hybrid retrieval with cached embeddings and eval-gated query generation."

Current decision: BM25 remains the baseline/control. The target product path is hybrid retrieval with constrained query variants, cached embeddings, eval-gated promotion, and a Pinecone-backed vector store behind a retrieval storage boundary. The 30-case expanded slice plus Pinecone parity supports moving hybrid+variants to candidate default, while requiring continued golden-set expansion and hosted-vector latency optimization before calling it production-final.
