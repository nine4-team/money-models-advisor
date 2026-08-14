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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-zrjffkba/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "diagnosable",
    "known_facts": {
      "business.business_type": "B2B cybersecurity compliance consultancy",
      "business.delivery_model": "expert-led readiness assessment, implementation project, and ongoing monitoring",
      "business.icp": "regional healthcare and financial-services firms preparing for audits",
      "economics.cac": 4500,
      "economics.first_30_day_gross_profit": 9000,
      "economics.gross_margin": 0.68,
      "economics.lifetime_gross_profit": 42000,
      "economics.monthly_recurring_gross_profit": 1800,
      "economics.payback_period_months": 1.0,
      "money_model.attraction_offer.description": "compliance readiness audit",
      "money_model.attraction_offer.exists": true,
      "money_model.attraction_offer.price": 1500,
      "money_model.continuity.description": "ongoing compliance monitoring",
      "money_model.continuity.exists": true,
      "money_model.continuity.price": 2500,
      "money_model.core_offer.description": "compliance implementation engagement",
      "money_model.core_offer.exists": true,
      "money_model.core_offer.price": 30000,
      "money_model.downsell.description": "self-directed remediation plan",
      "money_model.downsell.exists": true,
      "money_model.downsell.price": 5000,
      "money_model.upsell.description": "tabletop exercise and policy package",
      "money_model.upsell.exists": true,
      "money_model.upsell.price": 8000,
      "problem.recent_reported_symptoms": [
        "not enough qualified prospects enter sales conversations",
        "the team is considering several offer changes at the same time"
      ],
      "problem.reported_symptoms_count": 2,
      "problem.user_goal": "turn more qualified conversations into profitable long-term clients"
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

We do not get enough qualified conversations, but the clients we close are valuable. Which part of the offer stack is failing?
