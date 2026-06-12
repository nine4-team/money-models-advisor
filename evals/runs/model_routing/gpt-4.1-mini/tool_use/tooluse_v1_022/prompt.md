# Next-Action Eval Acting Prompt

You are the acting agent for a Money Model Advisor next-action eval case. Decide the ordered sequence of actions you would take for the current user turn before answering. All business state is provided inline below; you cannot run CLI commands in this harness, so report the actions you would take.

Action taxonomy (use these exact strings):

- `clarify`: ask the user for a missing fact that blocks a responsible answer.
- `update_snapshot`: persist a new business fact the user just provided.
- `read_snapshot`: read saved business economics and offer-stack state.
- `read_logs`: read prior-session records for earlier conversation context.
- `inspect_local_docs`: read the business's own local documents.
- `calculate`: run a deterministic metric calculation (CAC, gross profit, payback, CFA level).
- `diagnose`: run the deterministic money-model diagnosis over saved state.
- `search_source_material`: search the Money Models source corpus for citeable support.
- `compose_answer_from_state`: compose the answer from saved state and tool outputs.
- `answer_without_tool`: answer directly when no state or source support is needed.

Rules:

- Report only the actions this turn needs. Extra actions count against you.
- Do not use source-material search as a substitute for missing business facts.
- Do not search the source corpus for simple vocabulary answers.
- Each action needs `confidence`: `direct` when the provided state directly supports taking it, otherwise `inferred`.
- For tool-like actions (`update_snapshot`, `read_snapshot`, `read_logs`, `inspect_local_docs`, `calculate`, `diagnose`, `search_source_material`) with `direct` confidence, include `evidence_type` (one of `snapshot_field`, `session_file`, `local_doc`, `user_turn`, `planned_cli`) and `evidence_ref` naming the concrete field, file, or command you would rely on.

Respond with only one JSON object and no prose, in this shape:

{"actions": [{"action": "read_snapshot", "confidence": "direct", "evidence_type": "snapshot_field", "evidence_ref": "economics.cac"}, {"action": "compose_answer_from_state", "confidence": "inferred"}]}

Visible case context:

```json
{
  "case_id": "tooluse_v1_022",
  "conversation_context": "The user asks for a comparison of Money Models concepts.",
  "scenario_id": "1584_design",
  "user_turn": "what's the difference between an attraction offer and an upsell in this situation?"
}
```

Business snapshot (saved state):

```json
{
  "advisor_state": {
    "advisory_status": "insufficient_context",
    "likely_retrieval_layers": [],
    "missing_fields": [
      "economics.cac",
      "economics.first_30_day_gross_profit"
    ],
    "ready_for_offer_stack_diagnosis": true,
    "ready_for_payback_diagnosis": false,
    "retrieval_query_terms": [
      "premium full-service interior design firm for short-term rental and second-home projects",
      "STR and second-home owners with $80K-$200K+ project capacity",
      "full-service STR and second-home design",
      "talk through the money model"
    ]
  },
  "business": {
    "business_type": "premium full-service interior design firm for short-term rental and second-home projects",
    "delivery_model": "Lisa-led full-service design planning, procurement, and installation",
    "icp": "STR and second-home owners with $80K-$200K+ project capacity"
  },
  "economics": {
    "cac": null,
    "first_30_day_gross_profit": null,
    "gross_margin": null,
    "lifetime_gross_profit": null,
    "monthly_recurring_gross_profit": null,
    "payback_period_months": null
  },
  "field_sources": {
    "business.business_type": {
      "confidence": "high",
      "source_type": "local_docs"
    },
    "business.icp": {
      "confidence": "high",
      "source_type": "local_docs"
    },
    "money_model.core_offer.description": {
      "confidence": "high",
      "source_type": "local_docs"
    }
  },
  "money_model": {
    "attraction_offer": {
      "description": "STR Design Diagnostic with listing/photo audit and priority summary",
      "exists": true,
      "price": 597
    },
    "continuity": {
      "description": null,
      "exists": false,
      "price": null
    },
    "core_offer": {
      "description": "full-service STR and second-home design",
      "exists": true,
      "price": 15000
    },
    "downsell": {
      "description": null,
      "exists": false,
      "price": null
    },
    "upsell": {
      "description": "pre-designed room packages sold per room or bundle",
      "exists": true,
      "price": 5000
    }
  },
  "problem": {
    "diagnosed_constraints": [],
    "reported_symptoms": [],
    "user_goal": "talk through the money model"
  },
  "schema_version": "business_snapshot.v1"
}
```

Prior session records:

- none

Local business documents:

- none