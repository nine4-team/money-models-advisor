# Expanded Advisor Answer-Quality Audit

## Method

Twenty frozen `gpt-5.5` advisor turns were generated in fresh sanitized runtimes: four cases from each of five business contexts, comprising ten source-grounded answers, five deterministic calculations, and five clarification decisions. Source-grounded cases had to complete the current single-query hybrid path and cite retrieved passages; calculation cases had to record a recomputable CLI event; clarification cases had to record `clarify` without retrieval. Codex then reviewed each fixed answer against its captured snapshot, tool events, and exact retrieved text. Answer hashes bind every judgment to the reviewed output.

## Results

- Workflow-valid frozen runs: 20 / 20
- Semantic answer passes: 20 / 20
- Supported material claims: 22 / 22
- Latency: 71.9s p50 / 108.4s p95

| Answer category | Passed |
|---|---:|
| `source_grounded` | 10 / 10 |
| `calculation` | 5 / 5 |
| `clarification` | 5 / 5 |

| Business context | Passed |
|---|---:|
| `1584_design` | 4 / 4 |
| `b2b_consulting` | 4 / 4 |
| `ecommerce_skincare` | 4 / 4 |
| `fitness_coaching` | 4 / 4 |
| `saas_retention` | 4 / 4 |

## Failure Analysis

No semantic failures remain in the final 20-case suite. The initial frozen baseline passed 16 / 20: all source-grounded and calculation answers passed, while four clarification answers overpromised decisions from incomplete economics. The runtime now conditionally requires recurring gross profit when month-one gross profit does not recover CAC, and the advisor runbook distinguishes the first-month gate, recurring-payback branch, and downstream expected-value branch. A later countercase also caught and removed an arbitrary percentage-spend recommendation. The final outputs were regenerated blind and reviewed after freezing.

| Case | Category | Result | Audit rationale |
|---|---|---:|---|
| `answerquality_v1_001` | `source_grounded` | pass | The answer accurately applies the saved $1,000 CAC and $10,000 first-30-day gross profit, uses clear counterexamples, and preserves operational uncertainty. |
| `answerquality_v1_002` | `source_grounded` | pass | The answer uses saved offers, proposes a concrete implementation path, and correctly asks for gross profit and conversion rate before claiming a first-month profit lift. |
| `answerquality_v1_003` | `calculation` | pass | The result and explanation match the validated calculator event. |
| `answerquality_v1_004` | `clarification` | pass | The answer no longer asks for only one side of the comparison, distinguishes a capped discovery test from scaling, and identifies complete downstream inputs conditionally. |
| `answerquality_v1_005` | `source_grounded` | pass | The answer matches the month-four churn context and proposes bounded SaaS-specific variants without presenting them as proven. |
| `answerquality_v1_006` | `source_grounded` | pass | The answer correctly separates long-term value from timing and confines the recommendation to the next design problem. |
| `answerquality_v1_007` | `calculation` | pass | The answer reports and explains the tool-validated result accurately. |
| `answerquality_v1_008` | `clarification` | pass | The response holds spend steady, asks for the correct first inputs, and conditionally requests recurring gross profit rather than overpromising exact payback. |
| `answerquality_v1_009` | `source_grounded` | pass | The answer proposes an objective credit-first pilot and correctly asks for redemption economics before considering full cash refunds. |
| `answerquality_v1_010` | `source_grounded` | pass | The response gives a clear trigger, framing, and modular implementation tied to the saved coaching offer. |
| `answerquality_v1_011` | `calculation` | pass | The answer is concise and mathematically accurate. |
| `answerquality_v1_012` | `clarification` | pass | The previously passing countercase remains useful while now explicitly distinguishing measurement from scaling. |
| `answerquality_v1_013` | `source_grounded` | pass | The answer separates contribution profit from cash obligations, uses deterministic calculations, and recommends a bounded pilot. |
| `answerquality_v1_014` | `source_grounded` | pass | The recommendation uses saved offers, protects the full-price routine, and gives a clear customer-facing script. |
| `answerquality_v1_015` | `calculation` | pass | The answer accurately reports and explains the deterministic result. |
| `answerquality_v1_016` | `clarification` | pass | The answer clarifies without unnecessary retrieval, keeps spend unscaled, and requests conditionally complete economics. |
| `answerquality_v1_017` | `source_grounded` | pass | The answer applies saved prices, time-boxes the credit, and preserves the audit as a paid diagnostic. |
| `answerquality_v1_018` | `source_grounded` | pass | The rollout order matches the saved B2B offers and introduces each layer only after evidence from the prior one. |
| `answerquality_v1_019` | `calculation` | pass | The answer is concise and matches the validated event. |
| `answerquality_v1_020` | `clarification` | pass | The answer clarifies without retrieval, avoids a broad spend increase, and no longer omits implementation gross profit from the downstream branch. |

## Interpretation

The final suite supports the current source-grounded, calculation, and clarification paths across all five represented business contexts. This closes the identified answer-quality remediation item while preserving the failed baseline and intermediate countercase runs for inspection.

## Scope

This is a balanced 20-case regression, not a population estimate. Codex performed the semantic review rather than an independent human reviewer. The review artifact and frozen run directory are retained at `evals/advisor_answer_quality_expanded_final_audit.jsonl` and `evals/runs/answer_quality/expanded_v1_final`.
