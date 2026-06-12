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
  "adjudication_note": "Adjudicated after scenario_holdout run: the original expected_first_action was read_logs, but senior review concluded read_snapshot first is acceptable when logs are still read before final answer. Historical run artifacts were not changed.",
  "case_id": "tooluse_v1_023",
  "conversation_context": "Prior-session fixture contains ad-spend discussion and the snapshot contains current economics.",
  "scenario_id": "1584_design",
  "user_turn": "what did we already say about ads earlier?"
}
```

Business snapshot (saved state):

```json
{
  "advisor_state": {
    "advisory_status": "recommendable",
    "likely_retrieval_layers": [
      "unit-economics",
      "offers"
    ],
    "missing_fields": [],
    "ready_for_offer_stack_diagnosis": true,
    "ready_for_payback_diagnosis": true,
    "retrieval_query_terms": [
      "premium full-service interior design firm for short-term rental and second-home projects",
      "STR and second-home owners with $80K-$200K+ project capacity",
      "full-service STR and second-home design",
      "diagnose cash payback",
      "high_first_sale_margin",
      "CAC",
      "first 30 day gross profit",
      "payback period"
    ]
  },
  "business": {
    "business_type": "premium full-service interior design firm for short-term rental and second-home projects",
    "delivery_model": "Lisa-led full-service design planning, procurement, and installation",
    "icp": "STR and second-home owners with $80K-$200K+ project capacity"
  },
  "economics": {
    "cac": 1000,
    "first_30_day_gross_profit": 10000,
    "gross_margin": 0.769,
    "lifetime_gross_profit": null,
    "monthly_recurring_gross_profit": 0,
    "payback_period_months": 1.0
  },
  "field_sources": {
    "economics.cac": {
      "confidence": "medium",
      "source_type": "user_chat",
      "value_note": "Referral partner cost averaged to about $1k per client."
    },
    "economics.payback_period_months": {
      "confidence": "high",
      "source_type": "calculated"
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
    "diagnosed_constraints": [
      "high_first_sale_margin",
      "can_test_paid_acquisition"
    ],
    "reported_symptoms": [
      "wants to understand how much can be spent on acquisition"
    ],
    "user_goal": "diagnose cash payback"
  },
  "schema_version": "business_snapshot.v1"
}
```

Prior session records:

```json
{
  "fixture_id": "1584_ad_spend_context",
  "turns": [
    {
      "assistant_message": "CAC is currently represented as roughly $1,000 from referral partners, not paid ads.",
      "timestamp": "2026-06-05T22:46:39Z",
      "user_message": "referral partner CAC / Google Business Profile"
    },
    {
      "assistant_message": "With $10,000 first-30-day gross profit and $1,000 CAC, there is room to test paid acquisition carefully.",
      "timestamp": "2026-06-05T22:52:01Z",
      "user_message": "ok, so where does this leave us"
    }
  ]
}
```

Local business documents:

- none