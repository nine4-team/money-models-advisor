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
- The biggest modeling lesson is restraint: do not build a bespoke data structure around 1584's proposed "STR Design Diagnostic." That is a business-specific packaging idea, not a named Money Models framework. Scenario 002 exposed that the advisor may need to reason about economics for a specific proposed offer, but one scenario is not enough evidence to add a new schema branch. For now, record it as a modeling question and keep the canonical Money Models category as `attraction_offer` / front-end offer.
- The second product gap is recommendation retrieval precision and terminology discipline. The diagnosis searches were strong, but the recommendation search for a front-end/attraction-offer paid test retrieved some noisy offer chunks before more relevant attraction/decoy/free-with-consumption material. The final answer cited relevant chunks, but the candidate set was not as clean as it should be, and the write-up should not describe "diagnostic offer" as if it were a book term.
- The third product gap was fixture consistency. Scenario 003 surfaced a mismatch: `evals/fixtures/snapshots/1584_diagnosed.json` stored `payback_period_months` as `0.1`, while the CLI formula records `1.0` when CAC is recovered inside month one. The run used the CLI-calculated value, and the fixture has been corrected so future tests do not carry contradictory economics.
- Scenario 001 is still useful as a product run, but not as clean blind-eval evidence because the runner saw the rubric before acting. It should either be rerun blind or marked as a non-blind exploratory smoke.

## Scenario Summary

| Scenario | Status | Useful Behavior | Main Caveat |
|---|---|---|---|
| `productsmoke_v1_001` | completed, non-blind caveat | Gathered context, saved clear facts, avoided premature retrieval/calculation, asked for CAC next. | Runner saw rubric before acting; snapshot lacks acquisition-channel fields. |
| `productsmoke_v1_002` | completed, blind | Calculated and saved CAC, gross profit/margin, payback/CFA; delayed search until economics supported diagnosis/recommendation. | Business-specific offer economics should not trigger a bespoke schema change from one case; recommendation retrieval was noisy. |
| `productsmoke_v1_003` | completed, blind | Used diagnosed snapshot, handled continuity challenge, cited source-backed explanation, recorded complete traces. | Historical run surfaced a now-corrected fixture payback mismatch; citations support Money Models mechanics but are not domain-specific to interior-design diagnostics. |

## Decision

The advisor is directionally usable, but the next product fix should not be a trace viewer or a new business-specific data structure. The next fix is to inspect recommendation retrieval for front-end/attraction-offer searches. If repeated future scenarios show that economics must be tracked separately for generic Money Models offer slots, handle that as a separate schema-design decision rather than smuggling in a 1584-specific object.
