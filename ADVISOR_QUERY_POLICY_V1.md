# Advisor Query Policy v1

This policy defines how the advisor builds retrieval queries from `BusinessSnapshot`, `advisory_status`, diagnosed constraints, and the current user turn.

The advisor should not use the raw user message as the main retrieval query for diagnosis. Runtime queries are built from accepted snapshot state and the advisor's current intent.

## Inputs

- `BusinessSnapshot`
- `advisor_state.advisory_status`
- `problem.diagnosed_constraints`
- current user message
- current money-model stack shape

## Output Shape

```json
{
  "intent": "diagnostic_evidence",
  "layer": "unit-economics",
  "query": "CAC first 30 day gross profit payback period client financed acquisition coaching business implementation program",
  "reason": "Snapshot is diagnosable; retrieve unit-economics evidence before explaining the diagnosis."
}
```

## Retrieval Intents

| Intent | Purpose | Typical layer |
|---|---|---|
| `diagnostic_evidence` | Retrieve source material that explains how to interpret the business economics. | `unit-economics` |
| `recommendation_evidence` | Retrieve source material for the likely fix after the constraint is diagnosed. | `upsells`, `continuity`, `offers`, `downsells` |
| `framework_explanation` | Explain a named framework or concept. | inferred from framework |
| `framework_comparison` | Compare two named frameworks. | inferred from frameworks |

Retrieval evidence is saved in the session trace. It is not a `BusinessSnapshot` status.

## Status Policy

### `insufficient_context`

Do not retrieve by default. Ask for the next missing field.

Exception: if the current user message is clearly a teach/compare request, build `framework_explanation` or `framework_comparison` queries from the message.

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

The goal is to retrieve fix frameworks, not re-diagnose the economics.

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

## Framework Requests

If the user asks to explain a named framework, build `framework_explanation`.

Examples:

| User language | Layer | Query |
|---|---|---|
| rollover upsell | `upsells` | rollover upsell |
| classic upsell | `upsells` | classic upsell |
| anchor upsell | `upsells` | anchor upsell |
| payment plan | `downsells` | payment plans |
| continuity bonus | `continuity` | continuity bonus |
| attraction offer | `offers` | attraction offer |
| client financed acquisition / CFA | `unit-economics` | client financed acquisition CFA |

If the user asks to compare two frameworks, build one `framework_comparison` query per framework.

## Query Construction Rules

- Prefer accepted snapshot state over raw user wording.
- Include business type and core offer only as context terms, not as the center of the query.
- Keep query strings short enough to preserve the framework terms.
- Do not include unknown fields.
- Deduplicate terms.
- Emit multiple queries when one diagnosis suggests multiple fix paths.

