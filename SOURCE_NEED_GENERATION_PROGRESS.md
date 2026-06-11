# Source-Need Generation Progress

This tracker is for one problem only: when source-material search may be needed, whether the acting agent generates the right structured source need before query construction.

It is separate from:

- next-action classification: whether the agent should search at all
- search-query quality: whether a supplied source need becomes a useful corpus query
- retrieval-backend comparison: whether BM25, dense, or hybrid ranks chunks best

## Current Status

The source-need generation harness exists and has now been run with blind acting-agent traces:

- case set: `evals/advisor_source_need_cases.jsonl`
- trace capture helper: `scripts/capture_source_need_trace.py`
- scorer: `scripts/eval_source_need_generation.py`
- report: `evals/reports/advisor_source_need_generation.md`
- run artifacts: `evals/runs/source_need/pilot/`

The seed case set has 14 realistic turns:

- 10 cases where source-material search is expected
- 4 no-search controls where source search should not happen
- dev and scenario-holdout splits

Current scored result:

- scored runs: 14 / 14
- search decision accuracy: 100.0%
- false search rate: 0.0%
- missed search rate: 0.0%
- intent match on expected-search cases: 80.0%
- layer exact match on expected-search cases: 70.0%
- average layer recall on expected-search cases: 0.850
- average focus-term recall on expected-search cases: 0.410
- correct no-search controls: 100.0%

Interpretation: the agent-facing guidance is now good enough on the first-order question of whether source-material search is needed. The remaining weakness is precision in the generated source need, especially layer boundaries and exact focus-term coverage. Intent match improved after adding eval-only acceptable intent labels for the free-trial mixed case.

## Partial/Miss Case Interpretation

Senior review of the partial/miss cases:

- `sourceneed_v1_003`: keep expected `diagnostic_evidence`. The user asks how to interpret ad-spend capacity from known economics, not which offer fix to implement. Add alias credit for `paid acquisition capacity` as a match for `ad spend`.
- `sourceneed_v1_006`: keep expected `recommendation_evidence` and `continuity`. The user asks whether recurring maintenance or membership would help payback, so the source claim is about a continuity fix. Payback can be a focus term without adding the `unit-economics` layer.
- `sourceneed_v1_007`: keep expected `downsells`. Payment plans reduce immediate purchase friction and are therefore downsell-layer evidence, even when the underlying product stays the same.
- `sourceneed_v1_008`: keep expected layers `offers` and `downsells`, but allow both `teaching_evidence` and `recommendation_evidence` as acceptable intents. The user asks whether a free trial could work, which can reasonably require both concept explanation and recommendation support.
- `sourceneed_v1_010`: treat the low focus score as a metric false negative. `front-end offer`, `engagement`, and `STR owners` are reasonable concept matches for the expected front-end-offer and lead-engagement ideas, but exact substring scoring misses them.

Design decision: runtime should emit one primary `intent` per source need because `intent` means the retrieval objective for one search call, not the full conversational intent of the user's turn. Teaching, diagnosis, comparison, and recommendation ask the source corpus for different kinds of support. If one answer needs two different retrieval jobs, the planner should issue two source needs rather than one ambiguous mixed-intent source need. Eval labels can use optional `acceptable_intents` when more than one primary retrieval objective is defensible; that makes the label tolerant without changing the runtime meaning. This is now implemented for `sourceneed_v1_008`.

Post-refactor manual 1584 test note: a recommendation turn that mixed unit-economics focus terms with broad offer-stack layers retrieved mostly unit-economics chunks. The correct agent behavior is to split that answer into separate searches: one `diagnostic_evidence` SourceNeed for the unit-economics interpretation and one `recommendation_evidence` SourceNeed for the specific fix layer. The skill and operating guide now state this explicitly, and `turn record` is tested with multiple source events.

Senior review of the post-refactor batch: the agent/CLI boundary is sound and portfolio-positive, but the multi-source hardening is not behavior-validated yet. The current test proves `turn record` can persist multiple `source_events`; it does not prove that an acting agent will choose multiple SourceNeeds after the guidance change. The next best evidence is a post-hardening acting-agent regression for the 1584 "what should we fix first?" scenario that expects two searches: a diagnostic `unit-economics` SourceNeed and a recommendation SourceNeed for the specific fix layer. This is higher-priority hiring evidence than adding embeddings right now.

Implementation status: the source-event trace regression harness now exists. It uses `evals/advisor_source_event_cases.jsonl`, `scripts/capture_source_event_trace.py`, `scripts/eval_source_event_traces.py`, and `evals/reports/advisor_source_event_traces.md`. The first case is `sourceevents_v1_001`, the post-hardening 1584 "what should we fix first?" regression. The case is prepared but still needs a completed acting-agent trace before we can claim behavior validation.

Focus-term scoring should add agent-adjudicated concept coverage. Exact substring recall is useful for debugging query wording, but it is too brittle as the main quality score because it treats harmless wording differences as failures.

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
- acting-agent traces are captured **Done**
- search decision accuracy is high enough to avoid noisy retrieval-backend comparisons **Done**
- source-search cases have good intent/layer/focus-term scores **Partially done**

## Next Work

Tighten source-need precision before retrieval-backend comparisons:

- complete the post-hardening acting-agent trace for `sourceevents_v1_001`; expected trace has two source events: diagnostic `unit-economics` plus recommendation for the selected fix layer
- keep runtime `intent` as a single primary label, but add eval-only `acceptable_intents` for mixed cases
- refine layer guidance for payment-plan/free-trial cases so agents choose downsell/offer layers consistently
- add acting-agent cases or trace checks for turns that require multiple source-material searches
- add agent-adjudicated focus-term concept coverage, while keeping exact substring overlap as a debugging metric
- rerun the source-need eval after the taxonomy/scoring cleanup
