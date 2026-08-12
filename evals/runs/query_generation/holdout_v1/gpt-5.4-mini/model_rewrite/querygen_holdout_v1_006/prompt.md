You generate one query for searching a source corpus.

The system has already decided that source search is appropriate. Write the single
query most likely to retrieve passages that directly answer the user's current
question.

Use saved business facts only when they change what evidence is needed. Do not stuff
the query with background details merely because they are available. Do not answer the
question. Do not provide a rationale, subject label, namespace, filter, or multiple
queries. Do not invent facts. Do not use tools.

Return only the JSON object required by the response schema.

## Current user question

Skeptical leads need to experience our coaching before they will pay. What approach fits that problem?

## Saved business facts

```json
{
  "business": {
    "business_type": "boutique strength and nutrition coaching business",
    "delivery_model": "small-group training, nutrition coaching, and weekly accountability",
    "icp": "busy professional women seeking measurable strength and body-composition results"
  },
  "economics": {
    "cac": 320,
    "first_30_day_gross_profit": 900,
    "gross_margin": 0.72,
    "lifetime_gross_profit": 4200,
    "monthly_recurring_gross_profit": 150,
    "payback_period_months": 1.0
  },
  "money_model": {
    "attraction_offer": {
      "description": "free strength and nutrition assessment",
      "exists": true,
      "price": 0
    },
    "continuity": {
      "description": "ongoing training membership",
      "exists": true,
      "price": 249
    },
    "core_offer": {
      "description": "12-week coached transformation program",
      "exists": true,
      "price": 2400
    },
    "downsell": {
      "exists": false
    },
    "upsell": {
      "exists": false
    }
  },
  "problem": {
    "reported_symptoms": [
      "prospects are skeptical before experiencing the coaching",
      "some qualified prospects cannot pay the full program price immediately"
    ],
    "user_goal": "improve conversion and early customer value without making coaching feel cheaper"
  }
}
```
