# JD Requirements Audit

**Updated:** 2026-08-14

This file maps the Acquisition.com Senior AI Engineer role in
`JOB_DESCRIPTION.md` to current project evidence. It is a portfolio-scope audit,
not a claim that this local advisor has been deployed in production.

## Current position

The project is strongest on the parts of the role that can be demonstrated with
code and recorded experiments:

- an agent-operated workflow with a clear semantic-versus-deterministic boundary;
- a stateful CLI with calculations, retrieval, persistence, and trace validation;
- golden datasets and regression-oriented scorers for agent behavior and RAG;
- measured query-generation, chunking, embedding, hybrid-retrieval, Pinecone,
  namespace, latency, and model-routing decisions;
- cached embeddings and traceable evaluation artifacts.

The remaining portfolio gaps are narrower: broader end-to-end answer coverage,
one repeatable regression gate, and a final rendered narrative review. Metered agent
cost cannot be reported honestly while agent execution uses a subscription
harness, so it is deferred until a deployment path exposes billed calls.

## Requirement mapping

| JD area | Current evidence | Remaining work |
|---|---|---|
| Agentic workflows and tool use | The operating agent uses the Money Model Advisor skill and CLI. The agent chooses actions and writes answers; the CLI loads state, calculates, searches, validates, and records traces. | Expand end-to-end answer cases beyond the six-case seed audit. |
| RAG chunking | Five strategies were screened and replayed on the current 46-case path. Framework-aware chunking improved Useful@5 and reduced oversized chunks. | Preserve as a regression; revisit only when new failures justify it. |
| Query generation | Raw questions, unguided rewrites, and corpus-guided rewrites were compared under `gpt-5.5` and `gpt-5.4-mini` through BM25 and hybrid. Corpus guidance won across both models and retrievers. | Add genuinely new cases rather than retuning the existing 46. |
| Embedding selection | `text-embedding-3-small` and `text-embedding-3-large` were compared at 1,536 dimensions. Large improved Useful@5 from 78.7% to 86.5% and is the runtime default. | Preserve the frozen comparison and monitor cost if the corpus grows. |
| Hybrid retrieval | Hybrid preserves 100% Hit@5 and improves Useful@5 over BM25 for both guided query writers. BM25 remains the lexical control. | Add new failure-driven cases. |
| Pinecone and index management | Local and Pinecone stores share a retrieval boundary. The selected 204 framework-aware chunks were indexed and replayed on all 46 cases. | No additional backend work is required for the current portfolio scope. |
| Multiple namespaces | One namespace was compared with Unit Economics, Offers, Upsells, Downsells, and Continuity namespaces. The split did not improve quality, so the active path remains one unfiltered namespace. | Revisit only if corpus growth creates measurable interference. |
| Reranking | Reciprocal-rank fusion combines BM25 and vector rankings. A learned reranker was not adopted because the current evidence does not show a top-five ordering problem that warrants one. | Revisit if useful candidates regularly fail to enter the returned top five. |
| Golden datasets and automated scoring | `GOLDEN_DATASET.md` maps strict behavior cases, retrieval cases, trace cases, calculation checks, and semantic answer audits to scorers and reports. | Broaden business contexts and turn the stable subset into one regression command or CI job. |
| Retrieval metrics and latency | Current reports include Hit@1/3/5, first-useful rank, Useful@5, Noise@5, p50/p95 latency, cache behavior, and embedding cost estimates. Pinecone Large replay reached 86.1% Useful@5 at 1.13s p50 and 1.43s p95. | Consolidate promotion thresholds when the regression gate is added. |
| Model routing and tiering | On 48 balanced search-decision cases, `gpt-5.5` scored 48/48 and `gpt-5.4-mini` scored 47/48. Mini also found useful evidence within five hybrid results on all 46 query cases. The operating agent remains `gpt-5.5`; Mini is a bounded query-writer option. | Metered cost comparison remains unavailable in the subscription harness. |
| Observability | Session traces record actions, calculations, searches, inspected chunks, citations, and completed answers. Retrieval reports record quality, latency, embedding-cache activity, and estimated embedding cost. | A single regression summary with explicit pass/fail thresholds would make these signals easier to operate. |
| Reliability and regression detection | Unit tests and focused scorers validate formulas, request/trace agreement, citation provenance, retrieval choices, and saved artifacts. | Add one stable top-level regression command or CI job. |
| Multiple model providers | Historical provider experiments are not used as current product evidence because an equivalent same-harness comparison is unavailable. | Not required for completion; add only if comparable access becomes available. |
| TypeScript, API, and deployment surface | This repository is a Python, CLI-backed AI systems artifact. | A thin TypeScript or hosted surface is optional and should not duplicate the advisor logic. |

## Completion priorities

1. Finish the rendered narrative review.
2. Expand semantic answer-quality coverage with genuinely different business
   contexts and observed failures.
3. Add one repeatable regression gate over the stable local suites.
4. Report comparable billed agent cost only when the runtime exposes metered calls.

The first three items define the practical completion line for this repository.
Multi-provider access, a TypeScript surface, and a hosted deployment are optional
extensions, not reasons to keep the current portfolio project indefinitely open.
