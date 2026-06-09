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

Old keyword evidence-term experiments are archived under `archive/keyword-evidence-proxy/` and are not part of the active design.
Old provider-backed experiments are archived under `archive/provider-backed-experiments/` and are not part of the active design.
