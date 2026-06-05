# GPT-4o-mini vs GPT-5.5 Chunk Label Disagreements

## Summary

- Rows compared: 312
- Disagreements: 119
- Agreement: 61.86%

## Transition Counts

| GPT-4o-mini | GPT-5.5 | Rows |
|---:|---:|---:|
| 0 | 0 | 22 |
| 0 | 1 | 8 |
| 0 | 2 | 1 |
| 1 | 0 | 29 |
| 1 | 1 | 61 |
| 1 | 2 | 40 |
| 2 | 0 | 8 |
| 2 | 1 | 33 |
| 2 | 2 | 110 |

## Largest Disagreements

| ID | GPT-4o-mini | GPT-5.5 | GPT-5.5 Note |
|---|---:|---:|---|
| `paraphrase_buy_more_units::rollover-upsell:4` | 2 | 0 | Rollover credit is for applying a prior purchase toward another offer, not getting customers to buy more sessions up front. |
| `exact_client_financed_acquisition_levels::cac:12` | 2 | 0 | Discusses attraction offers and demand for CFA, but not the three client-financed acquisition levels. |
| `exact_client_financed_acquisition_levels::cac:0` | 2 | 0 | Defines and calculates CAC, but does not provide the client-financed acquisition levels. |
| `diagnostic_free_offer_overload::cac:4` | 0 | 2 | Directly addresses free offers lowering lead cost while creating too much volume if the business is not prepared to follow up. |
| `diagnostic_free_offer_overload::cac:11` | 2 | 0 | Discusses discount offers and card-on-file mechanics, not the free workshop volume, booking-rate, or support-load diagnosis. |
| `confusable_bonus_vs_discount::waived-fee:4` | 2 | 0 | Discusses fee-based stickiness and cancellation costs, a different mechanism than discount versus bonus retention. |
| `confusable_bonus_vs_discount::waived-fee:3` | 2 | 0 | Waived-fee commitment mechanics are adjacent retention guardrails, not the cheaper monthly versus recurring bonus choice. |
| `confusable_bonus_vs_discount::waived-fee:2` | 2 | 0 | Waived-fee explanation is about making leaving cost more than staying, not the queried discount-or-bonus choice. |
| `confusable_bonus_vs_discount::waived-fee:1` | 2 | 0 | Explains waived setup fees and cancellation terms, not continuity discounts or monthly value bonuses. |
| `situation_sales_team_discounting::payment-plans:8` | 2 | 1 | Gives seesaw payment-plan tactics for lowering monthly payment without lowering total value, useful but secondary. |
| `situation_sales_team_discounting::payment-plans:3` | 2 | 1 | Useful payment-term alternatives like credit card or layaway, but not as directly about avoiding discount training as earlier payment-plan chunks. |
| `situation_sales_team_discounting::payment-plans:2` | 1 | 2 | Directly shows reframing a higher anchored price into either prepay savings or spread payments, avoiding the feel of discounting after a no. |
| `situation_sales_team_discounting::payment-plans:1` | 1 | 2 | Directly says buyers often need lower payment now, not cheaper stuff, and recommends payment plans that preserve full or higher total price. |
| `situation_sales_team_discounting::pay-less-now:8` | 1 | 2 | Summarizes pay-less-now/pay-more-later as a structured choice with pay-now discount and bonuses, not an ad hoc hesitation discount. |
| `situation_sales_team_discounting::pay-less-now:3` | 1 | 2 | Gives concrete pay-later versus pay-now examples where the lower price is tied to paying now and added bonuses, not waiting for a deal. |
| `situation_saas_onboarding_commitment::waived-fee:3` | 1 | 2 | Directly provides example pricing and variables for waiving a setup fee in exchange for a commitment. |
| `situation_saas_onboarding_commitment::waived-fee:1` | 1 | 2 | Directly defines the waived-fee commitment offer and matches the setup-fee versus churn tradeoff in the query. |
| `situation_premium_option_makes_core_sell::classic-upsell:4` | 2 | 1 | Adjacent upsell guidance for done-for-you add-ons, but not the anchor framing that makes the core offer reasonable. |
| `situation_premium_option_makes_core_sell::buy-x-get-y:6` | 1 | 0 | Buy-X-get-Y/prepayment guidance, not presenting a premium option to anchor the core offer. |
| `situation_premium_option_makes_core_sell::buy-x-get-y:4` | 1 | 0 | Generic free-items-versus-discount framing, not anchor upsell. |
| `situation_premium_option_makes_core_sell::buy-x-get-y:3` | 1 | 0 | Buy-X-get-Y examples and prepayment, not premium-option anchoring. |
| `situation_physical_product_cash_gap::payment-plans:7` | 2 | 1 | Useful background on front-loading and seesaw framing, but it is less direct about immediate fulfillment costs than the layaway chunks. |
| `situation_physical_product_cash_gap::payment-plans:3` | 1 | 2 | Directly defines layaway for products and states the customer takes the risk instead of the business. |
| `situation_paid_ads_breakeven_slow::gross-profit:3` | 1 | 2 | Useful because it calculates service gross margin and gives a rule of thumb that service businesses should target at least 80 percent gross margin. |
| `situation_paid_ads_breakeven_slow::gross-profit:0` | 1 | 2 | Directly argues many businesses should make more gross profit per customer rather than obsessing over cheaper leads, matching the ad-CAC scenario. |
| `situation_paid_ads_breakeven_slow::context:1` | 1 | 2 | Directly explains customer-financed acquisition and why first-30-day gross profit must exceed CAC to scale paid ads. |
| `situation_paid_ads_breakeven_slow::cac:2` | 2 | 1 | Gives ways to lower CAC with better offers and free/new language, but the scenario more strongly points to improving first-30-day gross profit. |
| `situation_paid_ads_breakeven_slow::cac:12` | 2 | 1 | Explains CAC improvement via attraction offers, but the scenario also says clients do not buy more for months, making gross-profit/offer-stack fixes more central. |
| `situation_local_service_free_leads::cac:2` | 2 | 1 | Supports why free lowers CAC and increases demand, but does not address operational overload or filtering. |
| `situation_local_service_free_leads::cac:12` | 2 | 1 | Partially useful because it says free and discounted front ends can both work to improve CAC, but it does not solve operations overload. |
| `situation_gym_trial_no_show::free-trials:4` | 2 | 1 | Useful for handling trial users who like, hate, or do not use it, but less about changing the front-end offer. |
| `situation_gym_trial_no_show::cac:6` | 2 | 1 | Useful reminder that free can still work and friction can be added, but not specific to trial conversion structure. |
| `situation_gym_trial_no_show::buy-x-get-y:4` | 1 | 0 | Generic buy-X-get-Y offer framing, not gym trial no-show or conversion mechanics. |
| `situation_churn_month_four::continuity-discounts:2` | 1 | 2 | Directly useful for retention: apply discounts or free time at the end so customers earn it by paying through the term. |
| `situation_churn_month_four::continuity-bonus:6` | 1 | 2 | Directly recommends status or bonus milestones just after known churn points to pull members through the risky months. |
| `paraphrase_subscription_sells_bonus::waived-fee:5` | 1 | 0 | Summarizes waived-fee commitment offers, unrelated to positioning a membership around the included asset. |
| `paraphrase_subscription_sells_bonus::waived-fee:2` | 1 | 0 | Discusses onboarding fees and commitments, not how to market a membership around a recurring bonus asset. |
| `paraphrase_subscription_sells_bonus::continuity-offers:3` | 1 | 0 | Focuses on churn, lower rates, and big-head-long-tail economics rather than positioning the monthly asset as the selling point. |
| `paraphrase_subscription_sells_bonus::continuity-bonus:3` | 2 | 1 | Gives examples of one-time and monthly bonuses attached to continuity, but the strongest positioning advice is in adjacent chunks. |
| `paraphrase_old_buyers_new_version::ten-years-ten-minutes:2` | 1 | 2 | Identifies rollover upsells as crediting a previous purchase toward the next offer, which fits past buyers of an old version. |
