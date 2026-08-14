# Money Model Advisor Search Decision

Decide whether answering the user's request requires searching the Money Models
source material. This is the real advisor search gate, not an answer-writing task.

The current runtime rules are:

- Search when the answer needs Money Models support for a concept, comparison,
  diagnosis, or recommendation and the snapshot already holds enough relevant facts.
- Do not search instead of obtaining missing business facts or prior-session context.
- Do not search for a simple vocabulary answer that does not need a citation.

1. The deterministic harness has already loaded the current advisor state and
   recent turns through the real CLI. Use the provided context as authoritative.
2. Do not run tools. Do not search the Money Models corpus. Do not answer the user's question.
   Stop once you can choose the search gate.
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-0u3rmp4w/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "recommendable",
    "known_facts": {
      "business.business_type": "premium full-service interior design firm for short-term rental and second-home projects",
      "business.delivery_model": "Lisa-led full-service design planning, procurement, and installation",
      "business.icp": "STR and second-home owners with $80K-$200K+ project capacity",
      "economics.cac": 1000,
      "economics.first_30_day_gross_profit": 10000,
      "economics.gross_margin": 0.769,
      "economics.monthly_recurring_gross_profit": 0,
      "economics.payback_period_months": 1.0,
      "money_model.attraction_offer.description": "STR Design Diagnostic with listing/photo audit and priority summary",
      "money_model.attraction_offer.exists": true,
      "money_model.attraction_offer.price": 597,
      "money_model.continuity.exists": false,
      "money_model.core_offer.description": "full-service STR and second-home design",
      "money_model.core_offer.exists": true,
      "money_model.core_offer.price": 15000,
      "money_model.downsell.exists": false,
      "money_model.upsell.description": "pre-designed room packages sold per room or bundle",
      "money_model.upsell.exists": true,
      "money_model.upsell.price": 5000,
      "problem.diagnosed_constraints": [
        "high_first_sale_margin",
        "can_test_paid_acquisition"
      ],
      "problem.recent_reported_symptoms": [
        "wants to understand how much can be spent on acquisition"
      ],
      "problem.reported_symptoms_count": 1,
      "problem.user_goal": "diagnose cash payback"
    },
    "missing_fields": [],
    "ready_for_offer_stack_diagnosis": true,
    "ready_for_payback_diagnosis": true
  },
  "local_documents": {},
  "recent_turns": []
}
```

User request:

would a recurring maintenance or membership offer help our payback?
