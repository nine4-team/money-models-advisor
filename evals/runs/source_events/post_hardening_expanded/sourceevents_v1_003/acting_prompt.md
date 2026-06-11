# Source-Event Trace Acting Prompt

You are the acting agent for a Money Model Advisor source-event trace eval case.

Use the money-model-advisor skill and local CLI as needed. Expected source events are intentionally hidden.

Task: answer the user's turn using the post-refactor agent-operated workflow. If the answer needs source-material support, generate SourceNeeds, run source-material search, inspect chunks, answer with citations, and record the completed turn with `turn record`.

If one answer needs multiple retrieval jobs, run multiple searches and record one `source_events` entry per search. For example, a turn may need one diagnostic unit-economics search and one recommendation search for the selected fix layer.

Do not label a unit-economics search as recommendation evidence merely because the final answer recommends something. Use diagnostic evidence for the economics interpretation, then recommendation evidence for the concrete fix or action.

If you recommend a concrete Money Models move, source that move separately. Examples: diagnostic/front-end offer -> offers; post-sale add-on -> upsells; recurring maintenance -> continuity; payment plan/downsell -> downsells.

Do not create multiple recommendation SourceNeeds for the same fix layer unless they support genuinely different claims.

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/source_events/post_hardening_expanded/sourceevents_v1_003/business`

Visible case context:

```json
{
  "case_id": "sourceevents_v1_003",
  "conversation_context": "The snapshot is recommendable and already identifies strong first-sale economics. The user asks for a concrete way to increase first-30-day gross profit without redesigning the core service.",
  "scenario_id": "1584_design",
  "user_turn": "how should we increase first-30-day gross profit without changing the full-service offer?"
}
```

After acting, complete the trace with `scripts/capture_source_event_trace.py complete ...`. Do not look up expected labels.
