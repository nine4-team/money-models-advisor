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

A customer says the full routine costs too much. Could we remove one product and lower the price instead of discounting everything?

## Saved business facts

```json
{
  "business": {
    "business_type": "direct-to-consumer natural skincare brand",
    "delivery_model": "physical products shipped from third-party fulfillment",
    "icp": "adults with sensitive skin who want a simple recurring routine"
  },
  "economics": {
    "cac": 48,
    "first_30_day_gross_profit": 32,
    "gross_margin": 0.62,
    "lifetime_gross_profit": 210,
    "monthly_recurring_gross_profit": 28,
    "payback_period_months": 1.5714285714285714
  },
  "money_model": {
    "attraction_offer": {
      "description": "low-cost sensitive-skin sample kit",
      "exists": true,
      "price": 10
    },
    "continuity": {
      "description": "automatic refill subscription",
      "exists": true,
      "price": 55
    },
    "core_offer": {
      "description": "three-product starter routine",
      "exists": true,
      "price": 90
    },
    "downsell": {
      "description": "two-product essentials kit",
      "exists": true,
      "price": 55
    },
    "upsell": {
      "description": "premium five-product routine",
      "exists": true,
      "price": 160
    }
  },
  "problem": {
    "reported_symptoms": [
      "premium routine is difficult to advertise directly",
      "shipping and product costs consume a meaningful share of revenue"
    ],
    "user_goal": "improve front-end conversion without creating an inventory cash problem"
  }
}
```
