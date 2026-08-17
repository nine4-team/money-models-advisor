# Query Realism Methodology

## Purpose

The original `evals/golden.jsonl` set is a pilot set. It is useful for validating that the retrieval harness runs, but many queries name the same frameworks used in the corpus. That can inflate lexical retrieval results because BM25 is rewarded when the query repeats chapter titles or framework names.

The next retrieval benchmark should use realistic user-intent queries before selecting a dense, hybrid, fusion, or rerank strategy.

## Query Types

The draft realistic set lives in `evals/realistic_queries.jsonl`.

| Query Type | Purpose |
|---|---|
| `exact_framework` | Keeps a small number of direct framework-name lookups so named concepts still work. |
| `paraphrase` | Tests whether retrieval finds the right concept when the user describes it without naming it. |
| `business_situation` | Tests messy business context where the user describes symptoms, not frameworks. |
| `diagnostic_numeric` | Tests whether unit-economics questions retrieve the right metric and diagnostic material. |
| `confusable` | Tests near-neighbor concepts that are easy to mix up, such as payment plans vs feature downsells. |
| `noisy_vague` | Tests realistic typos, shorthand, incomplete phrasing, and casual user language. |

## Lexical-Overlap Audit

| Dataset | Queries | Type Mix | Avg Best Chapter-Name Overlap | Avg Candidate Chapter Overlap | Any Chapter Phrase Hit | Candidate Phrase Hit |
|---|---:|---|---:|---:|---:|---:|
| `pilot-golden` | 32 | pilot: 32 | 61.46% | 51.82% | 34.38% | 28.12% |
| `realistic-draft` | 36 | business_situation: 8, confusable: 6, diagnostic_numeric: 6, exact_framework: 6, noisy_vague: 4, paraphrase: 6 | 53.01% | 25.46% | 27.78% | 13.89% |

Interpretation: lower overlap is not automatically better; exact-framework queries should overlap. The purpose is to make the benchmark mix explicit so lexical lookup does not dominate the final retrieval decision.

## Highest Candidate-Overlap Queries

### pilot-golden

- `payback_definition` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: How do I shorten payback period with upsells in the first 30 days?
- `rollover_upsell` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: When should I use a rollover upsell?
- `free_offer_cac` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: Why do free offers lower CAC and what should I watch out for?
- `cac_fully_loaded` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: What costs should I include in fully loaded CAC?
- `payback_gross_profit_not_revenue` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: Why is payback period calculated from gross profit instead of revenue?
- `win_your_money_back` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: How does a win your money back offer work for a transformation business?
- `menu_upsell` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: How does the menu upsell use unsell prescribe preference and card on file?
- `payment_plans` (pilot): candidate overlap 100.00%; candidate phrase hit: True; query: How should payment plans handle customers who cannot afford the offer today?

### realistic-draft

- `exact_rollover_upgrade_existing_buyers` (exact_framework): candidate overlap 100.00%; candidate phrase hit: True; query: When should I use a rollover upsell for existing customers?
- `exact_menu_upsell` (exact_framework): candidate overlap 100.00%; candidate phrase hit: True; query: How does the menu upsell work?
- `exact_pay_less_now` (exact_framework): candidate overlap 100.00%; candidate phrase hit: True; query: When would I use pay less now, pay more later?
- `exact_continuity_discount` (exact_framework): candidate overlap 100.00%; candidate phrase hit: True; query: How do continuity discounts reduce churn?
- `situation_local_service_free_leads` (business_situation): candidate overlap 100.00%; candidate phrase hit: True; query: A free inspection gets us a lot of leads, but our team is buried with people who were never going to buy. How do we keep CAC low without drowning operations?
- `confusable_waived_fee_vs_pay_less_now` (confusable): candidate overlap 100.00%; candidate phrase hit: False; query: I want people to start with less cash up front, but I also need them committed to the recurring plan. Is that a waived setup fee thing or a pay-later thing?
- `situation_gym_trial_no_show` (business_situation): candidate overlap 50.00%; candidate phrase hit: False; query: We give away a free gym trial and get tons of signups, but half never show and the rest rarely convert. How should the front-end offer change?
- `situation_saas_onboarding_commitment` (business_situation): candidate overlap 50.00%; candidate phrase hit: False; query: Our software has setup work, but if we charge a setup fee fewer people start. If we waive it, people churn fast. Is there a way to create commitment without scaring them off?

## Labeling Rule

The fields `target_layer_hint` and `candidate_chapters` are reviewer orientation only. They are not final relevance labels.

Final retrieval selection should use chunk-level judgments:

| Label | Meaning |
|---:|---|
| 0 | The chunk is not useful for answering this query. |
| 1 | The chunk is partially useful or background context, but not enough by itself. |
| 2 | The chunk directly supports a good answer to the query. |

## Evaluation Procedure

1. Run each candidate retriever against the same realistic query set.
2. For each query, collect the top chunks returned by every candidate.
3. Dedupe by chunk ID.
4. Hide which retriever returned each chunk before review.
5. Label each query/chunk pair with the 0/1/2 rubric.
6. Score each retriever by the relevance grades of the chunks it ranked highly.

## Decision Rule

Do not select a final retriever from the pilot chapter-level metrics.

Use the pilot results only to show that the harness works and to identify candidate retrievers. Use realistic-query, chunk-level relevance judgments to choose among dense, hybrid, fusion, and rerank variants.

## Current Status

- Pilot query set: `evals/golden.jsonl`
- Draft realistic query set: `evals/realistic_queries.jsonl`
- Old keyword evidence experiments: `archive/keyword-evidence-proxy/`
