# Tool-Use Eval Implementation Plan

This plan upgrades the tool-use judgment eval from a useful debugging loop into a small but methodologically sound hiring-artifact eval.

The goal is not to build a production-scale benchmark. The goal is to demonstrate senior AI engineering judgment: separate tool selection from retrieval quality, avoid circular overclaiming, support multi-tool turns, measure failure modes, and show a clear before/after improvement path.

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
- keep `expected_first_action` because the first tool choice is often where bad behavior starts

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

## Actual Action Extraction

Define actual actions from the session trace and command history, not from subjective answer quality.

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
- false-search rate drops from baseline
- required actions are present for most dev/regression cases
- holdout results are at least directionally consistent with dev/regression results
- traces are clear enough to audit actual tool choice

V1 is not required to prove production robustness.

## Hiring Artifact Framing

In the final narrative, describe this as:

> a small-scale behavior eval that demonstrates the methodology for agent tool-use judgment, with a clear path to production scaling.

Do not describe it as:

> a comprehensive production benchmark.

The strength of the artifact is the thinking: precise problem decomposition, non-circular scoring, traceability, and before/after improvement.

## Next Steps

1. Create `evals/advisor_tool_use_cases.jsonl`.
2. Write `scripts/eval_tool_use_judgment.py`.
3. Generate the first baseline report.
4. Improve the skill/tool guidance from dev/regression failures.
5. Re-run and record before/after results.
