# Expanded Advisor Answer-Quality Baseline

## Method

Twenty frozen `gpt-5.5` advisor turns were generated in fresh sanitized runtimes: four cases from each of five business contexts, comprising ten source-grounded answers, five deterministic calculations, and five clarification decisions. Source-grounded cases had to complete the current single-query hybrid path and cite retrieved passages; calculation cases had to record a recomputable CLI event; clarification cases had to record `clarify` without retrieval. Codex then reviewed each fixed answer against its captured snapshot, tool events, and exact retrieved text. Answer hashes bind every judgment to the reviewed output.

## Results

- Workflow-valid frozen runs: 20 / 20
- Semantic answer passes: 16 / 20
- Supported material claims: 32 / 36
- Latency: 84.4s p50 / 115.8s p95

| Answer category | Passed |
|---|---:|
| `source_grounded` | 10 / 10 |
| `calculation` | 5 / 5 |
| `clarification` | 1 / 5 |

| Business context | Passed |
|---|---:|
| `1584_design` | 3 / 4 |
| `b2b_consulting` | 3 / 4 |
| `ecommerce_skincare` | 3 / 4 |
| `fitness_coaching` | 4 / 4 |
| `saas_retention` | 3 / 4 |

## Failure Analysis

All ten source-grounded answers and all five deterministic calculations passed. Four of five clarification answers failed for one shared reason: the advice correctly withheld a scale decision, but then requested too few economic inputs for the calculation it promised. CAC plus first-30-day gross profit can establish whether acquisition pays back inside one month. When it does not, exact payback also requires recurring gross profit. A downstream lead-value calculation likewise needs downstream gross profit, not only offer price and conversion rate.

Failure labels: `insufficient_restraint` 4, `unsupported_material_claim` 4.

| Case | Category | Result | Audit rationale |
|---|---|---:|---|
| `answerquality_v1_001` | `source_grounded` | pass | The answer accurately applies the saved $1,000 CAC and $10,000 first-30-day gross profit, explains why fulfillment cost matters, and binds its framework claims to supporting passages. |
| `answerquality_v1_002` | `source_grounded` | pass | The recommendation uses an offer already saved in the snapshot, applies the right framework, performs the ratio correctly, and avoids claiming the credit is profitable without considering fulfillment. |
| `answerquality_v1_003` | `calculation` | pass | The answer reports the validated deterministic result and clearly explains that recovery occurs inside the first month. |
| `answerquality_v1_004` | `clarification` | fail | The capped-test recommendation is sensible, but the final request is internally inconsistent and promises a decision from insufficient economics. |
| `answerquality_v1_005` | `source_grounded` | pass | The answer directly addresses month-four churn with the matching continuity pattern and adds a sensible safeguard against masking an onboarding or value problem. |
| `answerquality_v1_006` | `source_grounded` | pass | The diagnosis distinguishes total value from cash timing and correctly computes the gap. Citation completeness on the final intervention sentence could be improved, but the advice itself is supported by an inspected passage. |
| `answerquality_v1_007` | `calculation` | pass | The answer gives the correct validated result and shows the calculation in plain language. |
| `answerquality_v1_008` | `clarification` | fail | The hold recommendation is appropriate and the missing facts are accurately identified, but the answer overpromises an exact payback calculation from only two inputs. |
| `answerquality_v1_009` | `source_grounded` | pass | The response applies the right offer structure, gives objective conditions, and appropriately limits cash exposure while keeping the recommendation actionable. |
| `answerquality_v1_010` | `source_grounded` | pass | The recommendation is closely matched to both the saved business and the retrieved framework, with an explicit guardrail against making the original coaching purchase misleading. |
| `answerquality_v1_011` | `calculation` | pass | The answer accurately reports the tool-validated result and explains the one-month convention. |
| `answerquality_v1_012` | `clarification` | pass | The answer does not promise an exact multi-month payback value; it requests enough data for a conservative scale/no-scale decision based on first-month acquisition economics. |
| `answerquality_v1_013` | `source_grounded` | pass | The answer correctly distinguishes headline cash from reserved fulfillment obligations, performs the unit economics accurately, and recommends a bounded existing-customer pilot. |
| `answerquality_v1_014` | `source_grounded` | pass | The response uses the existing $55 essentials downsell, preserves the core outcome, and explains the comparison without inventing business facts. |
| `answerquality_v1_015` | `calculation` | pass | The answer reports and explains the validated deterministic calculation accurately. |
| `answerquality_v1_016` | `clarification` | fail | The no-scale recommendation is appropriately cautious, but the requested inputs are insufficient for the exact payback calculation the answer promises. |
| `answerquality_v1_017` | `source_grounded` | pass | The answer accurately applies the saved prices, recommends a clear expiration window, and does not misrepresent the audit as free. |
| `answerquality_v1_018` | `source_grounded` | pass | The response maps each saved B2B offer to the correct layer and recommends a constraint-driven rollout rather than unjustified simultaneous launch. |
| `answerquality_v1_019` | `calculation` | pass | The answer gives the correct tool-validated result without unnecessary claims. |
| `answerquality_v1_020` | `clarification` | fail | The bounded-test recommendation is sensible, but the answer promises a complete lead-economics decision without requesting implementation gross profit for the downstream branch it explicitly invokes. |

## Interpretation

The baseline supports the source-grounded recommendation and deterministic-calculation paths, but it does not yet support claiming complete answer quality. The clarification failure is general rather than case-specific, so the next step is to correct the input-sufficiency rule and rerun the clarification cases plus countercases without overwriting this baseline.

## Scope

This is a balanced 20-case regression, not a population estimate. Codex performed the semantic review rather than an independent human reviewer. The review artifact and frozen run directory are retained at `evals/advisor_answer_quality_expanded_baseline_audit.jsonl` and `evals/runs/answer_quality/expanded_v1`.
