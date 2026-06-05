# Advisor Query Policy v1

This policy defines how local corpus-search queries are built when the advisor decides that source material is needed for the current turn.

Current handoff note: the v1 implementation is still too blunt. The 1584 Design trace review in `ADVISOR_RETRIEVAL_HANDOFF.md` shows that retrieval is currently triggered more by snapshot readiness than by the specific current turn. Treat the policy below as the target direction, not proof that the implementation is finished.

The advisor should not use shallow keyword matching over the raw user message as the router. V1 should use the agent conversation as the advisor loop: the agent reads the conversation, the `BusinessSnapshot`, and available tools, then decides whether to clarify, calculate, diagnose, teach, compare, recommend, search source material, update the snapshot, or decline. Query construction happens only when that advisor loop chooses to search source material.

Deterministic rules are allowed only where the justification is strong:

- arithmetic and formulas, such as CAC payback and gross profit calculations
- narrow validated extraction, such as obvious dollar amounts
- schema/readiness checks, such as whether required snapshot fields exist
- query assembly from accepted snapshot facts and advisor-selected focus terms

Deterministic rules should not decide broad conversational intent, such as whether a user wants teaching versus diagnosis. That belongs to the agent-led advisor turn.

## Inputs

- `BusinessSnapshot`
- `advisor_state.advisory_status`
- `problem.diagnosed_constraints`
- advisor-selected tool intent and focus terms, when source search is needed
- current money-model stack shape

## Output Shape

```json
{
  "intent": "diagnostic_evidence",
  "layer": "unit-economics",
  "query": "CAC first 30 day gross profit payback period client financed acquisition coaching business implementation program",
  "reason": "Snapshot is diagnosable; search unit-economics source material before explaining the diagnosis."
}
```

## Retrieval Intents

| Intent | Purpose | Typical layer |
|---|---|---|
| `diagnostic_evidence` | Search for source material that explains how to interpret the business economics. | `unit-economics` |
| `recommendation_evidence` | Search for source material for the likely fix after the constraint is diagnosed. | `upsells`, `continuity`, `offers`, `downsells` |
| `teaching_evidence` | Search for source material for a concept the advisor chose to teach. | advisor-selected |
| `comparison_evidence` | Search for source material for concepts the advisor chose to compare. | advisor-selected |

Retrieval evidence is saved in the session trace. It is not a `BusinessSnapshot` status.

## Status Policy

### `insufficient_context`

Do not search by default. Ask for the next missing field.

Exception: if the advisor chooses to teach or compare and needs source evidence, build `teaching_evidence` or `comparison_evidence` from the advisor-selected focus terms and layer.

### `diagnosable`

Build one `diagnostic_evidence` query.

Layer:

- `unit-economics`

Core terms:

- `CAC`
- `first 30 day gross profit`
- `payback period`
- `client financed acquisition`
- `gross profit`

Add context terms when available:

- business type
- ICP
- core offer description

### `diagnosed`

Build one or more `recommendation_evidence` queries from `problem.diagnosed_constraints` and the current money-model stack.

The goal is to search for fix support, not re-diagnose the economics.

### `recommendable`

Build recommendation queries just like `diagnosed`. The difference is that stack context is complete enough to choose fixes with less ambiguity.

## Constraint Policy

| Diagnosed constraint | Snapshot condition | Layer | Query terms |
|---|---|---|---|
| `payback_not_recovered_without_recurring_gp` | `upsell.exists = false` | `upsells` | upsell after first sale, increase first 30 day gross profit, improve payback period |
| `payback_not_recovered_without_recurring_gp` | `continuity.exists = false` | `continuity` | continuity recurring gross profit, improve payback period, recurring offer |
| `slow_payback` | `upsell.exists = false` | `upsells` | upsell after first sale, improve cash payback, first 30 day gross profit |
| `slow_payback` | `continuity.exists = false` | `continuity` | continuity recurring gross profit, improve cash flow, payback period |
| `weak_first_sale_monetization` | any | `upsells` | increase first sale monetization, upsell offer, first 30 day gross profit |
| `low_gross_margin` | any | `unit-economics` | gross margin, gross profit, fulfillment cost, margin improvement |
| `weak_acquisition_offer` | any | `offers` | attraction offer, free trial, free giveaway, front end offer |
| `refund_or_payment_resistance` | any | `downsells` | downsell, payment plan, pay less now, waived fee |
| `retention_or_churn_issue` | any | `continuity` | continuity offer, retention, recurring value, churn |

If no constraint-specific rule matches, build a fallback `recommendation_evidence` query:

- layer: first `likely_retrieval_layers` value, or `unit-economics`
- query: diagnosed constraints + business type + core offer + user goal

## Teaching and Comparison

Teaching and comparison are valid advisor actions. They are not selected by keyword matching.

When the advisor chooses to teach with retrieval, the retrieval tool call should include:

- selected corpus `layer`
- `focus_terms`, such as the framework or concept to teach
- `reason`, explaining why teaching is the right next action

When the advisor chooses to compare with retrieval, the retrieval tool call should include the same fields for each concept or a combined query. Query construction then turns those focus terms into `teaching_evidence` or `comparison_evidence`.

## Query Construction Rules

- Prefer accepted snapshot state over raw user wording.
- Include business type and core offer only as context terms, not as the center of the query.
- Keep query strings short enough to preserve the advisor-selected focus terms.
- Do not include unknown fields.
- Deduplicate terms.
- Emit multiple queries when one diagnosis suggests multiple fix paths.
- Do not infer advisor action from keyword hits in the message.
