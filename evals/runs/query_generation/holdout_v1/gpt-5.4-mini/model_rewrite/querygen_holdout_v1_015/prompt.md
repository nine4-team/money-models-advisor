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

We do not get enough qualified conversations, but the clients we close are valuable. Which part of the offer stack is failing?

## Saved business facts

```json
{
  "business": {
    "business_type": "B2B cybersecurity compliance consultancy",
    "delivery_model": "expert-led readiness assessment, implementation project, and ongoing monitoring",
    "icp": "regional healthcare and financial-services firms preparing for audits"
  },
  "economics": {
    "cac": 4500,
    "first_30_day_gross_profit": 9000,
    "gross_margin": 0.68,
    "lifetime_gross_profit": 42000,
    "monthly_recurring_gross_profit": 1800,
    "payback_period_months": 1.0
  },
  "money_model": {
    "attraction_offer": {
      "description": "compliance readiness audit",
      "exists": true,
      "price": 1500
    },
    "continuity": {
      "description": "ongoing compliance monitoring",
      "exists": true,
      "price": 2500
    },
    "core_offer": {
      "description": "compliance implementation engagement",
      "exists": true,
      "price": 30000
    },
    "downsell": {
      "description": "self-directed remediation plan",
      "exists": true,
      "price": 5000
    },
    "upsell": {
      "description": "tabletop exercise and policy package",
      "exists": true,
      "price": 8000
    }
  },
  "problem": {
    "reported_symptoms": [
      "not enough qualified prospects enter sales conversations",
      "the team is considering several offer changes at the same time"
    ],
    "user_goal": "turn more qualified conversations into profitable long-term clients"
  }
}
```
