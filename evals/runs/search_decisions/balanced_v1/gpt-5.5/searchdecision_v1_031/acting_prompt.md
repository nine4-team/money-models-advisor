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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-kpr6xnpv/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "diagnosable",
    "known_facts": {
      "business.business_type": "boutique strength and nutrition coaching business",
      "business.delivery_model": "small-group training, nutrition coaching, and weekly accountability",
      "business.icp": "busy professional women seeking measurable strength and body-composition results",
      "economics.cac": 320,
      "economics.first_30_day_gross_profit": 900,
      "economics.gross_margin": 0.72,
      "economics.lifetime_gross_profit": 4200,
      "economics.monthly_recurring_gross_profit": 150,
      "economics.payback_period_months": 1.0,
      "money_model.attraction_offer.description": "free strength and nutrition assessment",
      "money_model.attraction_offer.exists": true,
      "money_model.attraction_offer.price": 0,
      "money_model.continuity.description": "ongoing training membership",
      "money_model.continuity.exists": true,
      "money_model.continuity.price": 249,
      "money_model.core_offer.description": "12-week coached transformation program",
      "money_model.core_offer.exists": true,
      "money_model.core_offer.price": 2400,
      "money_model.downsell.exists": false,
      "money_model.upsell.exists": false,
      "problem.recent_reported_symptoms": [
        "prospects are skeptical before experiencing the coaching",
        "some qualified prospects cannot pay the full program price immediately"
      ],
      "problem.reported_symptoms_count": 2,
      "problem.user_goal": "improve conversion and early customer value without making coaching feel cheaper"
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

give me a quick recap of the economics we already have for the coaching business
