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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-vbcwb1y2/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "diagnosable",
    "known_facts": {
      "business.business_type": "direct-to-consumer natural skincare brand",
      "business.delivery_model": "physical products shipped from third-party fulfillment",
      "business.icp": "adults with sensitive skin who want a simple recurring routine",
      "economics.cac": 48,
      "economics.first_30_day_gross_profit": 32,
      "economics.gross_margin": 0.62,
      "economics.lifetime_gross_profit": 210,
      "economics.monthly_recurring_gross_profit": 28,
      "economics.payback_period_months": 1.5714285714285714,
      "money_model.attraction_offer.description": "low-cost sensitive-skin sample kit",
      "money_model.attraction_offer.exists": true,
      "money_model.attraction_offer.price": 10,
      "money_model.continuity.description": "automatic refill subscription",
      "money_model.continuity.exists": true,
      "money_model.continuity.price": 55,
      "money_model.core_offer.description": "three-product starter routine",
      "money_model.core_offer.exists": true,
      "money_model.core_offer.price": 90,
      "money_model.downsell.description": "two-product essentials kit",
      "money_model.downsell.exists": true,
      "money_model.downsell.price": 55,
      "money_model.upsell.description": "premium five-product routine",
      "money_model.upsell.exists": true,
      "money_model.upsell.price": 160,
      "problem.recent_reported_symptoms": [
        "premium routine is difficult to advertise directly",
        "shipping and product costs consume a meaningful share of revenue"
      ],
      "problem.reported_symptoms_count": 2,
      "problem.user_goal": "improve front-end conversion without creating an inventory cash problem"
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

Our premium routine is hard to advertise. Could a stripped-down starter get people into a useful comparison?
