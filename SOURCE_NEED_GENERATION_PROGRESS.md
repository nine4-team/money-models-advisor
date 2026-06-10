# Source-Need Generation Progress

This tracker is for one problem only: when source-material search may be needed, whether the acting agent generates the right structured source need before query construction.

It is separate from:

- next-action classification: whether the agent should search at all
- search-query quality: whether a supplied source need becomes a useful corpus query
- retrieval-backend comparison: whether BM25, dense, or hybrid ranks chunks best

## Current Status

The source-need generation harness exists:

- case set: `evals/advisor_source_need_cases.jsonl`
- trace capture helper: `scripts/capture_source_need_trace.py`
- scorer: `scripts/eval_source_need_generation.py`
- report: `evals/reports/advisor_source_need_generation.md`

The seed case set has 14 realistic turns:

- 10 cases where source-material search is expected
- 4 no-search controls where source search should not happen
- dev and scenario-holdout splits

The current report is inventory-only. No acting-agent source-need `run.json` artifacts have been captured yet.

## What A Source Need Represents

A source need is the structured retrieval plan the acting agent generates before search:

- `intent`: why source material is needed
- `layers`: which Money Models corpus layer or layers to search
- `focus_terms`: the concepts the source material should support

Example:

```json
{
  "intent": "teaching_evidence",
  "layers": ["unit-economics"],
  "focus_terms": ["gross profit", "fulfillment cost", "CAC", "payback period"]
}
```

## Evaluation Strategy

Each case gives the acting agent conversation context, snapshot state, and the current user turn. Expected labels are hidden from the acting agent.

The acting agent should produce:

- `source_search_decision`: whether source-material search is needed
- `source_need`: null when search is not needed, otherwise an object with intent, layers, and focus terms

Metrics:

- search decision accuracy
- false search rate
- missed search rate
- intent match on search-expected cases
- layer exact match and layer recall
- focus-term recall
- correct no-search controls

## Done Criteria

For the first v1 pass:

- case labels validate **Done**
- report generation works without external model-service calls **Done**
- acting-agent traces are captured **Not yet**
- search decision accuracy is high enough to avoid noisy retrieval-backend comparisons **Not yet**
- source-search cases have good intent/layer/focus-term scores **Not yet**

## Next Work

Capture acting-agent source-need traces under `evals/runs/source_need/`, then score them with:

```bash
python3 scripts/capture_source_need_trace.py prepare sourceneed_v1_001
python3 scripts/capture_source_need_trace.py complete \
  evals/runs/source_need/pilot/sourceneed_v1_001 \
  --source-search-decision true \
  --source-need '{"intent":"teaching_evidence","layers":["unit-economics"],"focus_terms":["gross profit","fulfillment cost","CAC","payback period"]}'
python3 scripts/eval_source_need_generation.py
```

If source-need generation is weak, revise the skill or operating guide. If it is strong, proceed to retrieval-backend comparisons on the same source needs.
