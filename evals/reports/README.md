# Evaluation Reports

This directory holds experiment reports that justify architecture choices with measured comparisons.

Each report should use this structure:

```text
# Experiment Name

## Hypothesis

## Variants

## Dataset Slice

## Metrics

## Results

## Decision

## Failure Analysis

## Next Experiment
```

Recommended metrics:

- `router_accuracy`
- `hit@1`
- `hit@5`
- `mrr`
- `ndcg@10`
- `faithfulness`
- `structured_output_validity`
- `p50_latency_ms`
- `p95_latency_ms`
- `required_claim_support_coverage`
- `next_action_correctness`
- `answer_usefulness`

The goal is to make RAG architecture decisions the way an ML workflow makes model or hyperparameter decisions: by comparing variants under the same dataset, metrics, and adoption threshold.

The active retrieval-support guardrail is required-claim support coverage. Required supported claims live in `evals/obligations.jsonl`; review them with `PYTHONPATH=src python3 scripts/review_obligations.py`, then score accepted labels with `PYTHONPATH=src python3 scripts/score_obligation_support.py`. Use `--include-proposed` only when a future label batch has unreviewed proposed rows.

For active local retrieval checks, use:

```bash
PYTHONPATH=src python3 scripts/audit_query_realism.py
PYTHONPATH=src python3 scripts/eval_retrieval.py
PYTHONPATH=src python3 scripts/score_obligation_support.py
```

For active next-action classification checks, use:

```bash
python3 scripts/capture_tool_use_trace.py prepare tooluse_v1_001
python3 scripts/eval_tool_use_judgment.py
```

`capture_tool_use_trace.py prepare` creates an isolated eval directory plus an acting prompt that hides expected labels. After the acting agent records workflow evidence, use `capture_tool_use_trace.py complete <run_dir> ...` to validate and write `run.json`.

`eval_tool_use_judgment.py` validates `evals/advisor_tool_use_cases.jsonl` and scores any saved `run.json` traces under `evals/runs/next_action/`. If no traces exist yet, the report is case inventory only, not behavior results.

For active source-search query-quality checks, use:

```bash
python3 scripts/eval_search_query_quality.py --query-source reference \
  --report evals/reports/advisor_search_query_quality.md

python3 scripts/eval_search_query_quality.py --query-source generated \
  --report evals/reports/advisor_search_query_quality_generated.md
```

`eval_search_query_quality.py` validates `evals/advisor_search_query_cases.jsonl` and runs local BM25 search over heading-aware chunks. Reference mode asks whether reviewer-authored, source-specific queries can retrieve useful chunks. Generated mode asks whether the current runtime query builder can do the same from snapshot fixtures plus advisor-selected source needs. Known-useful chunk labels are seed labels for query development, not exhaustive relevance judgments.

For active source-need generation checks, use:

```bash
python3 scripts/capture_source_need_trace.py prepare sourceneed_v1_001
python3 scripts/capture_source_need_trace.py complete \
  evals/runs/source_need/taxonomy_v2/sourceneed_v1_001 \
  --source-search-decision true \
  --source-need '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["gross profit","fulfillment cost","CAC","payback period"]}'
python3 scripts/eval_source_need_generation.py
```

`capture_source_need_trace.py prepare` creates an isolated eval directory plus an acting prompt that hides expected labels. `complete` records the acting agent's source-search decision and generated source need. `eval_source_need_generation.py` validates `evals/advisor_source_need_cases.jsonl` and scores saved acting-agent `run.json` artifacts under `evals/runs/source_need/taxonomy_v2/` by default. It tests whether the acting agent decides if source search is needed and, when it is, generates intent, layer, and focus-term structure before query construction.

## Source-Event Trace Eval

```bash
python3 scripts/capture_source_event_trace.py prepare sourceevents_v1_001
python3 scripts/capture_source_event_trace.py complete \
  evals/runs/source_events/post_hardening/sourceevents_v1_001 \
  --actions-json '["read_snapshot","calculate","diagnose","search_source_material","search_source_material","turn_record"]' \
  --source-events-json '[{"source_need":{"intent":"diagnostic_evidence","layers":["unit-economics"],"focus_terms":["CAC","payback period"]},"query":"CAC payback period","chunks":[{"id":"payback-period:0"}]},{"source_need":{"intent":"recommendation_evidence","layers":["upsells"],"focus_terms":["upsell","first 30 day gross profit"]},"query":"upsell first 30 day gross profit","chunks":[{"id":"upsells:0"}]}]'
python3 scripts/eval_source_event_traces.py
```

`capture_source_event_trace.py prepare` creates an isolated eval directory plus an acting prompt that hides expected source-event labels. `complete` records the completed turn's actions, source events, and cited chunk IDs. `eval_source_event_traces.py` validates `evals/advisor_source_event_cases.jsonl` and scores saved `run.json` artifacts under `evals/runs/source_events/`. It tests whether an acting agent records distinct source events when one answer needs multiple retrieval jobs.

Old keyword evidence-term experiments are archived under `archive/keyword-evidence-proxy/` and are not part of the active design.
Old provider-backed experiments are archived under `archive/provider-backed-experiments/` and are not part of the active design.
