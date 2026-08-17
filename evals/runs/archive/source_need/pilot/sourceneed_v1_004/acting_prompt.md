# Source-Need Generation Acting Prompt

You are the acting agent for a Money Model Advisor source-need generation eval case.

Use the money-model-advisor skill and local CLI as needed. Expected labels are intentionally hidden.

Task: decide whether Money Models source-material search is needed for the current turn. If search is needed, generate a structured source need with `intent`, `layers`, and `focus_terms`. If search is not needed, set source need to null.

Do not use source-material search as a substitute for missing business facts. If the current turn needs missing economics, offer-stack facts, prior-session context, or deterministic math before an answer can be responsibly given, choose no source search for this step.

Keep layers minimal. Include only the corpus layers needed to support the source-backed claim; extra layers reduce precision.

Allowed intents:

- `teaching_evidence`
- `diagnostic_evidence`
- `comparison_evidence`
- `recommendation_evidence`

Allowed layers:

- `unit-economics`
- `offers`
- `upsells`
- `downsells`
- `continuity`

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/source_need/pilot/sourceneed_v1_004/business`

Visible case context:

```json
{
  "case_id": "sourceneed_v1_004",
  "conversation_context": "The snapshot has offer-stack context but no economics. The user asks to compare two Money Models concepts.",
  "scenario_id": "1584_design",
  "user_turn": "what's the difference between an attraction offer and an upsell in this situation?"
}
```

After acting, complete the trace with `scripts/capture_source_need_trace.py complete ...`. Do not look up expected labels.
