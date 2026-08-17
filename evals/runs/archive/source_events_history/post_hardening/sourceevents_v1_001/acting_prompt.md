# Source-Event Trace Acting Prompt

You are the acting agent for a Money Model Advisor source-event trace eval case.

Use the money-model-advisor skill and local CLI as needed. Expected source events are intentionally hidden.

Task: answer the user's turn using the post-refactor agent-operated workflow. If the answer needs source-material support, generate SourceNeeds, run source-material search, inspect chunks, answer with citations, and record the completed turn with `turn record`.

If one answer needs multiple retrieval jobs, run multiple searches and record one `source_events` entry per search. For example, a turn may need one diagnostic unit-economics search and one recommendation search for the selected fix layer.

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/source_events/post_hardening/sourceevents_v1_001/business`

Visible case context:

```json
{
  "case_id": "sourceevents_v1_001",
  "conversation_context": "The snapshot is recommendable for 1584 Design. Prior context includes referral-partner CAC and paid-acquisition capacity discussion. The user asks for the next priority.",
  "scenario_id": "1584_design",
  "user_turn": "what should we fix first?"
}
```

After acting, complete the trace with `scripts/capture_source_event_trace.py complete ...`. Do not look up expected labels.
