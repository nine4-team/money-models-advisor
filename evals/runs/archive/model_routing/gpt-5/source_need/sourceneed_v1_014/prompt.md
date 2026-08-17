# Source-Need Generation Acting Prompt

You are the acting agent for a Money Model Advisor source-need generation eval case.


Task: decide whether Money Models source-material search is needed for the current turn. If search is needed, generate a structured source need with `intent`, `layers`, and `focus_terms`. If search is not needed, set source need to null.

Do not use source-material search as a substitute for missing business facts. If the current turn asks for a business recommendation that depends on missing economics, offer-stack facts, prior-session context, or deterministic math before an answer can be responsibly given, choose no source search for this step.

Do use source-material search when the snapshot or prior-session context already contains enough facts for a source-backed explanation, diagnosis, comparison, or recommendation. A missing optional field should not block search when the user is asking for conceptual source support.

Do not search for simple vocabulary answers that can be answered directly without citation. Source search is for source-backed advisory claims, not every definition.

Keep layers minimal. Include only the corpus layers needed to support the source-backed claim; extra layers reduce precision.

Choose intent by retrieval job, not by the mood of the final answer:

- `teaching_evidence`: explain a Money Models concept or framework.
- `diagnostic_evidence`: support interpretation of known business economics or constraints.
- `comparison_evidence`: compare two concepts, options, or layers.
- `recommendation_evidence`: source support for a concrete next move after enough business facts are known.

Choose layers by the mechanism the source material must support:

- front-end attraction offer -> `offers`
- post-sale add-on or premium next offer -> `upsells`
- payment plan, pay-less-now option, or friction-reducing alternative -> `downsells`
- recurring maintenance, membership, or repeat post-purchase service -> `continuity`
- CAC, gross profit, payback, or acquisition capacity interpretation -> `unit-economics`

Use payback or CAC as focus terms without adding `unit-economics` when the source claim is about a concrete fix mechanism such as continuity or upsells.

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


Visible case context:

```json
{
  "case_id": "sourceneed_v1_014",
  "conversation_context": "The snapshot has offer-stack context but no economics. The user asks whether to run ads next month.",
  "scenario_id": "1584_design",
  "user_turn": "should we start running ads next month?"
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

All business state is provided inline below; you cannot run CLI commands in this harness.

Respond with only one JSON object and no prose, in this shape:

{"source_search_decision": true, "source_need": {"intent": "...", "layers": ["..."], "focus_terms": ["..."]}}

or, when source search is not needed:

{"source_search_decision": false, "source_need": null}