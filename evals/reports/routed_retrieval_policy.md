# Routed Retrieval Policy

## Purpose

Test whether a production-style router can choose diagnose-first retrieval from query text alone, without reading the eval `query_type` label.

## Router

Route to `diagnose-rewrite-bm25` when the query contains all three signals: a number, a business metric term, and diagnostic intent language.

- Routed queries: 6
- Expected diagnostic numeric queries: 6
- False positives vs eval query type: 0
- False negatives vs eval query type: 0


## Overall Results

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.6500 | 0.7667 | 0.5280 |
| `dense-default` | 0.7478 | 0.8611 | 0.6247 |
| `hybrid-default` | 0.7161 | 0.8667 | 0.6141 |
| `routed-dense-or-diagnose-rewrite` | 0.8187 | 0.8889 | 0.6383 |

## By Query Type nDCG@5

| Query type | BM25 | Dense | Hybrid | Routed policy |
|---|---:|---:|---:|---:|
| `business_situation` | 0.728 | 0.797 | 0.768 | 0.797 |
| `confusable` | 0.548 | 0.767 | 0.718 | 0.767 |
| `diagnostic_numeric` | 0.702 | 0.489 | 0.624 | 0.914 |
| `exact_framework` | 0.595 | 0.788 | 0.632 | 0.788 |
| `noisy_vague` | 0.729 | 0.848 | 0.767 | 0.848 |
| `paraphrase` | 0.598 | 0.815 | 0.786 | 0.815 |

## Routed Queries

| Query | Original text |
|---|---|
| `diagnostic_low_first_month_gp` | CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck? |
| `diagnostic_high_revenue_low_margin` | We charge $1,000 and spend about $700 delivering the service. Ads cost $180 per customer. Everyone says CAC is fine, but cash still feels tight. What metric am I missing? |
| `diagnostic_ltv_good_payback_bad` | Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on? |
| `diagnostic_free_offer_overload` | Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working? |
| `diagnostic_continuity_discount_math` | Members pay $99/month. Most cancel after month three. If we offer a permanent discount after month three, what are we trying to improve? |
| `diagnostic_cfa_level_goal` | If it costs $500 to acquire a customer and the first 30 days produce $1,100 in gross profit, what does that imply about our acquisition engine? |

## Decision

The router trigger matches the current diagnostic-numeric eval labels, and the routed policy improves the full realistic-query score by preserving dense retrieval for normal queries while using diagnose-first retrieval for numeric diagnostics.
