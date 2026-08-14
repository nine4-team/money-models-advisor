# Golden Dataset Suite

This project uses a golden-dataset suite to evaluate the Money Model Advisor as an agent-operated, CLI-backed RAG system. The suite is intentionally small enough for a portfolio project, but it is structured like a production eval loop: each case file targets a specific product risk, each scorer produces an auditable report, and design decisions are recorded from measured behavior rather than vibes.

The target job description calls for golden datasets, retrieval metrics, automated quality scoring, regression detection, cached embeddings, and cost-aware AI systems. This file is the map from that requirement to the project artifacts.

## Definition

A golden dataset is a versioned set of examples with expected behavior, labels, scoring logic, reports, and decision notes.

In this repo, golden data can include:

- realistic user turns;
- fixture snapshots and conversation context;
- expected agent actions;
- expected `SearchRequest` query content;
- expected source-event traces;
- known-useful source chunks;
- required-claim support labels;
- adjudication notes when labels are corrected.

The labels are not all the same kind of truth. Some are strict behavioral expectations, such as "do not search source material for this turn." Others are seed relevance labels, such as "this chunk is known useful," where the set is useful but not exhaustive. Reports should say which kind of label they are using.

## Dataset Lineage

Datasets, labels, and experiments are different units. An experiment may reuse one dataset, and one case may carry several labels; their counts should not be added together.

| Dataset | Units | Primary Use | Status |
|---|---:|---|---|
| `evals/advisor_tool_use_cases.jsonl` | 24 turns | General next-action behavior | Active component suite. |
| `evals/advisor_search_decision_cases.jsonl` | 48 turns | Search/no-search model comparison | Active. Balanced across 24 search-required and 24 search-prohibited cases in five business contexts. |
| `evals/golden.jsonl` | 32 queries | Initial local BM25 smoke test and chunking comparison | Pilot. Uses known-subject filters and chapter-level labels. Keep as a smoke baseline, not the current retrieval decision set. |
| `evals/obligations.jsonl` | 65 claim labels on the same 32 queries | Required-claim coverage for the pilot BM25 path | Historical guardrail, not 65 additional user cases. |
| `evals/advisor_search_query_cases_enriched_labels.jsonl` plus `evals/query_generation/query_generation_holdout_v1.jsonl` | 46 turns: 30 base + 16 expansion | Query approach, query-writing model, and BM25-vs-hybrid comparison | Active retrieval suite. Uses saved snapshot context, one unfiltered query, and audited passage-level usefulness labels. Canonical report: `evals/reports/query_generation_current.md`. |
| `evals/advisor_calculation_trace_cases.jsonl` | 5 turns | Calculation trace integrity | Active; 5/5 pass. |
| `evals/advisor_source_event_cases.jsonl` | 6 turns | Search trace integrity and search/no-search sequencing | Active. Six blind runs pass 6/6 on the current one-query `SearchRequest` contract; two answer-key corrections are disclosed in the report. |
| `evals/advisor_answer_quality_audit.jsonl` | 6 audited answers / 14 source-backed claims | Recommendation usefulness and semantic citation support | Active seed regression. Current answers pass 6/6 for correctness/usefulness and 14/14 audited claims are supported. Codex is the single semantic reviewer. |
| `evals/advisor_product_smoke_scenarios.jsonl` | 3 multi-turn sessions | End-to-end product behavior | Historical exploratory evidence. One run was non-blind and all predate the current single-query path. |

### Experiments That Reuse Those Datasets

- The full query approach × query model × retriever matrix reuses the same 46 retrieval cases for every condition.
- The agent search-decision comparison uses the same frozen 48 cases for both OpenAI models. Report: `evals/reports/search_decision_model_comparison.md`.
- Chunking and Pinecone infrastructure revalidation reuse the 46 active cases and the frozen winning queries. Reports: `evals/reports/active_query_chunking_revalidation.md`, `evals/reports/active_query_pinecone_revalidation.md`, and `evals/reports/pinecone_candidate_depth_optimization.md`.
- Embedding selection also reuses those 46 frozen queries. Large at 1,536 dimensions
  raises local Useful@5 from 78.7% to 86.5%; the isolated Pinecone replay reaches
  86.1% at 1.13s p50 / 1.43s p95. Reports:
  `evals/reports/embedding_model_comparison.md` and
  `evals/reports/pinecone_large_embedding_revalidation.md`.
- `evals/advisor_source_need_cases.jsonl`, `evals/advisor_query_variants_v2.jsonl`, and `evals/realistic_queries.jsonl` document earlier design stages. SourceNeed and multi-query filtering are retired product paths; the realism file is an audit draft, not a scored retrieval benchmark.

## Evaluation Ladder

1. Agent behavior: should the agent read state, inspect files or logs, calculate, diagnose, search, clarify, or answer?
2. Retrieval construction: which chunking strategy, query-generation method, and retriever should the product use?
3. Infrastructure: does the selected path preserve quality and acceptable latency on Pinecone, and does namespace partitioning help?
4. Model routing: which model tier can perform orchestration or bounded query writing without unacceptable quality loss?
5. Trace and answer quality: are calculations, searches, citations, and recommendations complete and supported?

Agent behavior, source-event traces, and the 46-case retrieval matrix are the strongest component results. Chunking and Pinecone latency/namespaces have now been replayed on that single-query path. The six-case current-path answer audit is a useful seed regression; broader end-to-end coverage remains open.

## Agent Search-Decision Evidence

`gpt-5.5` and `gpt-5.4-mini` each completed one blind pass over a frozen 48-case
suite: 24 cases require source search and 24 prohibit it. Five business contexts
each contain both labels. The deterministic harness loaded current advisor state,
recent turns, and local documents; the model made only the semantic search decision.
Retrieval, answer generation, shell use, evaluator labels, and prior trials were
excluded.

`gpt-5.5` scored 48/48 overall, finding all 24 required searches and avoiding all
24 prohibited searches. Mini scored 47/48, finding 23/24 required searches and
avoiding all 24 prohibited searches. Mini's one false negative was audited against
the current rule and business context; the answer key did not require correction.
This supports `gpt-5.5` as the operating agent. Mini remains supported for bounded
query writing by the separate 46-case retrieval experiment.

Current report: `evals/reports/search_decision_model_comparison.md`.

## Label Strength

Not every metric should be interpreted the same way.

- Tool-use cases and source-event cases are strict behavioral tests.
- The retired source-need labels are historical semantic expectations. They do not define the current query contract.
- Known-useful chunks in search-query cases are seed relevance labels, not exhaustive relevance judgments.
- Required-claim labels are human or agent-adjudicated support labels for specific claims, not a complete map of every useful chunk in the corpus.
- Exact focus-term recall is a debugging signal. Concept coverage with rationale is the stronger semantic signal.

When a report depends on non-exhaustive labels, the conclusion should be framed as an engineering signal rather than a production-quality benchmark.

## Development Rules

Before changing advisor behavior, identify which product risk the change is supposed to improve and which golden dataset should catch regressions.

Use an acting-agent test-fix loop for product workflow hardening:

1. Run blind acting agents on realistic turns.
2. Inspect saved traces, not only final answers.
3. Classify failures as path plumbing, tool choice, query generation, retrieval, trace shape, or answer quality.
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

## Query Generation Evidence

The current experiment asks how to generate good queries from the real product input:
the user question plus the normal saved snapshot. It compares the raw question, an
unguided model rewrite, and a model rewrite using a combined corpus guide. Each method
produces one query, sees no reviewer fields, and applies no subject filter. Every saved
query is run unchanged through BM25 and hybrid retrieval over the framework-aware
chunks used by the product.

Before finalizing the scores, returned passages were audited for both false negatives
and false positives. Missing directly useful passages were added, overly broad labels
were removed, and the corrected shared labels were applied to every method. No queries
were regenerated and retrieval was not rerun.

Across all 46 hybrid cases, final Hit@1/Hit@3/Hit@5 is 63.0%/80.4%/87.0% for the
raw question, 80.4%/91.3%/93.5% for the unguided `gpt-5.5` rewrite, and
93.5%/97.8%/100.0% for the corpus-guided `gpt-5.5` rewrite. Useful@5 is 50.9%,
62.6%, and 78.7%, respectively. Corpus guidance also leads the raw and unguided
conditions under BM25, so the method decision is not backend-dependent. Queries and
retrieval results were frozen before the method-neutral false-negative and
false-positive audits. Codex performed those semantic audits rather than an independent
human reviewer. The corpus-guided rewrite remains the selected CLI method.

With that method fixed, `gpt-5.4-mini` was compared with `gpt-5.5`. Across all 46
hybrid cases, Mini reached 91.3% Hit@1, 100.0% Hit@3, and 100.0% Hit@5 versus
93.5%, 97.8%, and 100.0% for `gpt-5.5`. Mini returned 185 useful passages and
`gpt-5.5` returned 181 in 230 slots.
Mini was slower and used more Codex-reported tokens in this harness, so query writing
remains inside the existing `gpt-5.5` orchestration turn rather than adding a separate
model call. Mini remains a validated bounded query-writer option.

The unguided rewrite was then repeated with Mini as an approach-robustness check.
Across all 46 hybrid cases, guided Mini improved Hit@1 from 76.1% to 91.3%, Hit@5
from 91.3% to 100.0%, and Useful@5 from 62.6% to 80.4%. The approach choice therefore
survives the model change; the narrative presents approach selection and model
selection as separate controlled questions.

Current report: `evals/reports/active_framework_retrieval_matrix.md`.
