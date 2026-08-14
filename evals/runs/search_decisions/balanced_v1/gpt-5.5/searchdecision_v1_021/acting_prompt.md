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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-j_ckonh6/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "diagnosable",
    "known_facts": {
      "business.business_type": "B2B inventory-planning SaaS",
      "business.delivery_model": "cloud software with guided onboarding and customer success",
      "business.icp": "multi-location specialty retailers with small operations teams",
      "economics.cac": 2800,
      "economics.first_30_day_gross_profit": 1100,
      "economics.gross_margin": 0.75,
      "economics.lifetime_gross_profit": 18000,
      "economics.monthly_recurring_gross_profit": 900,
      "economics.payback_period_months": 2.888888888888889,
      "money_model.attraction_offer.description": "paid inventory cleanup pilot",
      "money_model.attraction_offer.exists": true,
      "money_model.attraction_offer.price": 500,
      "money_model.continuity.description": "monthly software and customer-success subscription",
      "money_model.continuity.exists": true,
      "money_model.continuity.price": 1200,
      "money_model.core_offer.description": "inventory planning software subscription",
      "money_model.core_offer.exists": true,
      "money_model.core_offer.price": 1200,
      "money_model.downsell.exists": false,
      "money_model.upsell.description": "implementation and analytics package",
      "money_model.upsell.exists": true,
      "money_model.upsell.price": 4000,
      "problem.recent_reported_symptoms": [
        "many customers cancel during the fourth month",
        "new-customer acquisition requires more cash than month-one gross profit"
      ],
      "problem.reported_symptoms_count": 2,
      "problem.user_goal": "reduce month-four churn and improve acquisition payback"
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

what CAC do we currently have saved for the SaaS business?
