# Advisor Product-Smoke V1

## Scope

This stage evaluates the advisor as a product across realistic multi-turn sessions. It is not a replacement for component evals. Component evals ask whether individual mechanisms work: tool choice, source needs, query quality, calculation traces, and source-event traces. Product-smoke sessions ask whether those mechanisms combine into advice a user would trust.

## Scenario Set

- Case file: `evals/advisor_product_smoke_scenarios.jsonl`
- Run directory: `evals/runs/product_smoke/v1/`
- Scenarios: 3

## Product-Quality Rubric

Review each completed session for:

- Context handling: asks for missing facts or inspects available context before diagnosing.
- State handling: saves explicit business facts and calculated economics when appropriate.
- Tool judgment: calculates, searches, clarifies, or answers at the right time.
- Search quality: source searches have focused SourceNeeds and executed query variants.
- Citation quality: cited chunks plausibly support the claims being made.
- Recommendation quality: advice is specific to the business and not generic.
- Conversation quality: handles challenge/pushback directly and names what would change the recommendation.
- Trace completeness: every turn is recorded with complete actions, source events, calculation events, and final answer.

## Current Status

Runs complete.

- `productsmoke_v1_001`: completed, but compromised as a blind eval because the runner saw rubric/failure-mode fields before acting.
- `productsmoke_v1_002`: completed as a blind run.
- `productsmoke_v1_003`: completed as a blind run.

## Findings

- Overall product behavior was promising. Across the sessions, the advisor used saved state, avoided premature source search when economics were missing, calculated CAC/gross margin/payback/CFA when numbers appeared, recorded calculation events, generated source events with executed query variants, cited inspected chunks, and handled recommendation pushback.
- The biggest product gap is snapshot schema expressiveness. Scenario 002 needed offer-specific economics for the diagnostic offer: price, fulfillment cost, and gross margin. The current snapshot has global `economics.gross_margin`, so the runner stored diagnostic-offer margin globally with a scope caveat. That is awkward and can mislead later diagnosis if a front-end offer margin differs from full-service project margin.
- The second product gap is recommendation retrieval precision. The diagnosis searches were strong, but the recommendation search for a diagnostic/front-end paid test retrieved some noisy offer chunks before more relevant attraction/decoy/free-with-consumption material. The final answer cited relevant chunks, but the retrieval candidate set was not as clean as it should be.
- The third product gap is fixture consistency. Scenario 003 surfaced a mismatch: `evals/fixtures/snapshots/1584_diagnosed.json` stored `payback_period_months` as `0.1`, while the CLI formula records `1.0` when CAC is recovered inside month one. The run used the CLI-calculated value. The fixture should be corrected so future tests do not carry contradictory economics.
- Scenario 001 is still useful as a product run, but not as clean blind-eval evidence because the runner saw the rubric before acting. It should either be rerun blind or marked as a non-blind exploratory smoke.

## Scenario Summary

| Scenario | Status | Useful Behavior | Main Caveat |
|---|---|---|---|
| `productsmoke_v1_001` | completed, non-blind caveat | Gathered context, saved clear facts, avoided premature retrieval/calculation, asked for CAC next. | Runner saw rubric before acting; snapshot lacks acquisition-channel fields. |
| `productsmoke_v1_002` | completed, blind | Calculated and saved CAC, gross profit/margin, payback/CFA; delayed search until economics supported diagnosis/recommendation. | Offer-specific economics do not fit cleanly in snapshot; recommendation retrieval was noisy. |
| `productsmoke_v1_003` | completed, blind | Used diagnosed snapshot, handled continuity challenge, cited source-backed explanation, recorded complete traces. | Fixture payback mismatch; citations support Money Models mechanics but are not domain-specific to interior-design diagnostics. |

## Decision

The advisor is directionally usable, but the next product fix should not be a trace viewer. The highest-leverage improvement is to add offer-level economics to the snapshot model, then rerun the product-smoke session that exposed the issue. After that, fix the stale payback fixture and inspect recommendation retrieval for diagnostic/front-end offer searches.
