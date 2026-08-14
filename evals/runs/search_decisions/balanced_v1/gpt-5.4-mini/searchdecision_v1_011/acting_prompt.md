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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-u1xvg89g/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "insufficient_context",
    "known_facts": {
      "business.business_type": "premium full-service interior design firm for short-term rental and second-home projects",
      "business.delivery_model": "Lisa-led full-service design planning, procurement, and installation",
      "business.icp": "STR and second-home owners with $80K-$200K+ project capacity",
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
      "problem.user_goal": "talk through the money model"
    },
    "missing_fields": [
      "economics.cac",
      "economics.first_30_day_gross_profit"
    ],
    "ready_for_offer_stack_diagnosis": true,
    "ready_for_payback_diagnosis": false
  },
  "local_documents": {
    "business-profile.md": "# 1584 Design Business Profile\n\n1584 Design is a premium full-service interior design firm for short-term rental and second-home projects.\n\nThe target client is an owner of large STR properties or second homes with the budget for full-service design, procurement, and installation.\n",
    "product-ladder.md": "# Product Ladder\n\nDraft ladder:\n\n1. STR Design Diagnostic: listing and photo audit, likely $597 to $997.\n2. Pre-designed room packages: $1,200 to $1,800 per room or $5,000 to $7,000 as a bundle.\n3. Full-service design: planning, procurement, and installation.\n",
    "services-and-pricing.md": "# Services And Pricing\n\nThe core offer is full-service STR and second-home design.\n\nDraft pricing:\n\n- Design fee: $15,000 to $60,000 depending on project scope.\n- Typical project budget: $80,000 to $160,000.\n- Ideal project budget: $150,000 to $200,000 or more.\n"
  },
  "recent_turns": []
}
```

User request:

what's our current pricing again?
