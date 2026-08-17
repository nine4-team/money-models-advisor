# Source-Event Trace Acting Prompt

You are the acting agent for a Money Model Advisor source-event trace eval case.

Consult the money-model-advisor skill before you act, then use the local CLI to carry out the workflow. The skill and search-request rules are the authoritative runtime instructions. Expected source events are intentionally hidden.

Task: answer the user's turn using the active agent-operated workflow. If the answer needs source-material support, write one corpus-guided `SearchRequest.query` per evidence job, run `search --search-request-json`, inspect chunks, answer with citations, and record the completed turn with `session finish`.

If one answer needs multiple evidence jobs, run multiple searches and record one `source_events` entry per search. Do not use the legacy `SourceNeed`, subject-filter, or query-variant fields.

Use `intent` only as the closest trace label. Preserve the complete evidence need in `query`; intent does not control scoring or retrieval.

Business dir: `<repo>/evals/runs/source_events/search_request_v1/sourceevents_v1_005/business`

Visible case context:

```json
{
  "case_id": "sourceevents_v1_005",
  "conversation_context": "The snapshot is recommendable, but the user asks a conceptual teaching question rather than asking for diagnosis or implementation advice.",
  "label_audit": {
    "audited_at": "2026-08-13",
    "correction": "removed an unnecessarily prescriptive query term",
    "reason": "The frozen query retrieved directly useful definition evidence; requiring the phrase core offer tested wording rather than retrieval intent."
  },
  "scenario_id": "1584_design",
  "user_turn": "what is a front-end offer in plain English?"
}
```

After acting, complete the trace with `scripts/capture_source_event_trace.py complete ...`. Do not look up expected labels.

## Noninteractive completion requirement

Do not edit project source files. Work only inside the prepared business and run directories.
After `session finish`, use the returned `session_path` to create the eval artifact:

```bash
PYTHONPATH=src python3 scripts/capture_source_event_trace.py complete <repo>/evals/runs/source_events/search_request_v1/sourceevents_v1_005 --session-path <session_path> --notes 'blind Codex acting-agent run'
```

You must create `run.json` before returning. Your final response should only summarize the recorded action.
