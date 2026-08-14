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
3. Do not inspect any path outside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-search-gate-fo355lkp/runtime`. There are no evaluation labels or
   prior examples inside this directory.

Current business context:

```json
{
  "advisor_state": {
    "advisory_status": "insufficient_context",
    "known_facts": {},
    "missing_fields": [
      "problem.user_goal",
      "business.business_type",
      "business.icp",
      "money_model.core_offer.description",
      "money_model.attraction_offer.exists",
      "money_model.upsell.exists",
      "money_model.downsell.exists",
      "money_model.continuity.exists",
      "economics.cac",
      "economics.first_30_day_gross_profit"
    ],
    "ready_for_offer_stack_diagnosis": false,
    "ready_for_payback_diagnosis": false
  },
  "local_documents": {},
  "recent_turns": []
}
```

User request:

what does CAC stand for?
