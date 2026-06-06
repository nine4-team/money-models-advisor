# Next-Action Classification Eval Implementation Plan

This plan upgrades the next-action classification eval from a useful debugging loop into a small but methodologically sound hiring-artifact eval.

The goal is not to build a production-scale benchmark. The goal is to demonstrate senior AI engineering judgment: separate next-action classification from source-search query generation, avoid circular overclaiming, support multi-action turns, measure failure modes, and show a clear before/after improvement path.

## Eval Subject

This plan evaluates one thing: next-action classification.

Question:

```text
Given the conversation context and saved snapshot state, did the agent choose the correct next action label or action sequence for the current turn?
```

This plan does not evaluate source-search query quality. Query generation is evaluated separately in `SEARCH_QUERY_QUALITY_PROGRESS.md`, and only for cases where the correct next action is `search_source_material`.

The labels test conformance to the documented Money Model Advisor policy. They are not a claim about the one universally correct way every assistant should behave.

## Scope

V1 artifact scale:

- roughly 20-30 cases
- based on 1584 Design traces plus realistic synthetic follow-ups
- project-authored labels, validated by trace inspection
- enough to demonstrate the method and catch real failures

Production scale note:

- a production eval would expand to more businesses, more reviewers, more adversarial cases, and a larger frozen holdout
- the portfolio write-up should state this explicitly instead of pretending the small eval is a production benchmark

## Action Taxonomy

Use these action labels:

| Action | Meaning |
|---|---|
| `clarify` | Ask for the next missing or ambiguous business fact |
| `update_snapshot` | Save accepted business context |
| `read_snapshot` | Read saved business facts |
| `read_logs` | Inspect prior advisor turns |
| `inspect_local_docs` | Agent reads local business docs before saving facts |
| `calculate` | Run deterministic math or use calculated snapshot fields |
| `search_source_material` | Search the Money Models corpus for citeable source chunks |
| `answer_directly` | Answer from conversation/snapshot without a tool |

## Case Schema

Create `evals/advisor_tool_use_cases.jsonl`.

Each row should use this shape:

```json
{
  "case_id": "tooluse_v1_001",
  "split": "dev",
  "scenario_id": "1584_design",
  "turn_type": "saved_fact_lookup",
  "conversation_context": "The user previously said referral partners cost about $1k per client.",
  "snapshot_state": "Snapshot has CAC=$1k and first-30-day gross profit=$10k.",
  "user_turn": "what happened to the $1k we pay to referral partners?",
  "required_actions": ["read_snapshot"],
  "allowed_actions": ["read_logs", "answer_directly"],
  "forbidden_actions": ["search_source_material"],
  "expected_first_action": "read_snapshot",
  "search_allowed": false,
  "label_rationale": "The user is asking about saved business context, not Money Models source material.",
  "ambiguity": "low",
  "severity_if_wrong": "high"
}
```

Design choice:

- score required, allowed, and forbidden actions instead of a single `expected_action`
- this handles valid multi-step turns such as `read_snapshot -> calculate -> answer_directly`
- keep `expected_first_action` because the first action choice is often where bad behavior starts

## Case Balance

The first v1 case set should include at least two cases for each major action class:

| Action class | Minimum v1 cases |
|---|---:|
| `clarify` | 2 |
| `update_snapshot` | 2 |
| `read_snapshot` or `read_logs` | 2 |
| `inspect_local_docs` | 2 |
| `calculate` | 2 |
| `search_source_material` | 2 |
| `answer_directly` | 2 |

Include control cases:

- at least two negative controls where `search_source_material` is clearly wrong
- at least two positive controls where `search_source_material` is clearly required

## Split Strategy

Use a tiny split structure to demonstrate eval discipline without overbuilding:

| Split | Purpose | Suggested v1 size |
|---|---|---:|
| `dev` | Cases used to inspect failures and improve skill/tool guidance | 12-18 |
| `regression` | Cases for previously observed bugs, especially generic repeated search | 4-6 |
| `holdout` | Cases not used while tuning; run after changes as a generalization check | 4-6 |

Important:

- It is okay for v1 holdout to be small.
- The write-up should not overclaim from the holdout.
- The point is to show the method: tune on dev/regression, then sanity-check on untouched cases.

## Scoring

Create `scripts/eval_tool_use_judgment.py`.

Inputs:

- `evals/advisor_tool_use_cases.jsonl`
- actual trace/action records from the current run

Output:

- `evals/reports/advisor_tool_use_judgment.md`
- optionally `evals/runs/tool_use_judgment_*.json`

Metrics:

- first-action accuracy
- required-action recall
- forbidden-action violation rate
- false-search rate
- missed-search rate
- full-sequence pass rate
- per-turn-type breakdown
- trace completeness

Definitions:

- false search: `search_source_material` appears when it is forbidden
- missed search: `search_source_material` is required but absent
- required-action recall: required actions present in the actual action sequence
- full-sequence pass: all required actions present and no forbidden actions present
- trace completeness: actual actions can be recovered from logs without guessing

V1 thresholds:

- regression false-search rate on cases where search is forbidden: 0
- forbidden source search on saved-context lookup cases: 0
- trace completeness: at least 95%
- required-action recall on dev/regression: at least 80%
- holdout results are reported descriptively and are not used for a strong generalization claim

## Actual Action Extraction

Define actual actions from the session trace and command history, not from subjective answer quality. The eval report must include the case ID, expected actions, actual actions, trace path or run ID, and failure rationale for every failed case.

Mapping:

- `retrieval_queries` or `evidence` present -> `search_source_material`
- calculator action or deterministic payback/gross-margin computation -> `calculate`
- snapshot read command -> `read_snapshot`
- logs command -> `read_logs`
- snapshot field update -> `update_snapshot`
- local file reads in business directory -> `inspect_local_docs`
- assistant asks for missing field and no other stronger tool action occurs -> `clarify`
- assistant answers from available context without tool use -> `answer_directly`

If a trace cannot be classified, mark trace completeness as failed and record the case for logging improvement.

## Ambiguity Handling

Use the `ambiguity` field to avoid fake precision:

| Ambiguity | Scoring rule |
|---|---|
| `low` | Include in headline metrics. Score normally. |
| `medium` | Include in headline metrics, but use `allowed_actions` to avoid penalizing reasonable alternate paths. Do not penalize first action unless it is materially harmful or forbidden. |
| `high` | Exclude from headline metrics. Report qualitatively as an analysis case. |

High-ambiguity cases can be useful for design discussion, but they should not drive the headline score.

## Baseline And Improvement Loop

1. Build the eval cases and scorer.
2. Run current behavior as the baseline.
3. Produce a report with failures by split and turn type.
4. Improve skill instructions or CLI affordances based on dev/regression failures.
5. Re-run dev and regression cases.
6. Run holdout only after the improvement pass.
7. Document before/after metrics.

Do not tune directly on holdout failures. If a holdout failure reveals a new class of issue, move it into a future dev/regression set and create fresh holdout cases before making stronger claims.

## Success Criteria For V1

V1 is successful if it shows:

- repeated generic source search is reduced or eliminated on non-search turns
- regression false-search rate on search-forbidden cases reaches 0
- no forbidden source search on saved-context lookup cases
- required-action recall is at least 80% on dev/regression cases
- trace completeness is at least 95%
- holdout results are reported descriptively and do not immediately contradict the dev/regression improvement

V1 is not required to prove production robustness.

## Hiring Artifact Framing

In the final narrative, describe this as:

> a small-scale next-action classification eval, with source-search query generation evaluated separately and a clear path to production scaling.

Do not describe it as:

> a comprehensive production benchmark.

The strength of the artifact is the thinking: precise problem decomposition, non-circular scoring, traceability, and before/after improvement.

## Next Steps

1. Create `evals/advisor_tool_use_cases.jsonl`.
2. Write `scripts/eval_tool_use_judgment.py`.
3. Generate the first baseline report.
4. Improve the skill/tool guidance from dev/regression failures.
5. Re-run and record before/after results.
