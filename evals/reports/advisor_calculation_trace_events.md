# Advisor Calculation-Trace Eval

## Scope

This eval checks completed advisor-turn traces for deterministic math. It verifies that when an acting agent uses the CLI `calculate` operation, the saved turn records the metric, exact inputs, and numeric output in `calculation_events`.

It does not run an agent and does not call external model services. Acting agents complete traces separately; this scorer validates the resulting `run.json` artifacts.

## Dataset

- Cases: 5
- Splits: `trace_schema_regression`: 5
- Case file: `evals/advisor_calculation_trace_cases.jsonl`
- Run directory: `evals/runs/calculation_trace/subagent_v1`

## Validation

- Status: passed
- Scorer: `scripts/eval_calculation_trace_events.py`
- Command: `python3 scripts/eval_calculation_trace_events.py --runs-dir evals/runs/calculation_trace/subagent_v1`

## Run Coverage

- Scored runs: 5 / 5
- Missing runs: 0

## Metrics

- Case pass rate: 100.0%
- Failure count: 0

## Case Table

| Case | Expected Calculation Behavior | Actual Calculation Events | Status |
|---|---|---:|---|
| `calctrace_v1_001` | Payback from CAC and first-month gross profit | 1 | `passed` |
| `calctrace_v1_002` | Gross profit and gross margin | 2 | `passed` |
| `calctrace_v1_003` | CFA level plus diagnosis | 1 | `passed` |
| `calctrace_v1_004` | No calculation for a plain-English definition | 0 | `passed` |
| `calctrace_v1_005` | CAC calculation plus snapshot update | 1 | `passed` |

## Notes

The first subagent pass exposed two evaluator calibration issues, not product failures:

- `calctrace_v1_001` expected `0.1` months, but the CLI payback formula intentionally records payback as `1.0` when CAC is recovered inside month one.
- `calctrace_v1_002` differed only by floating-point precision on gross margin, so the scorer now uses a small numeric tolerance.

One subagent initially nested `calculation_events` under `metadata`; `session finish` rejected the trace, the agent corrected it, and the final run passed. That is the desired behavior: the CLI catches trace-shape mistakes instead of silently saving ambiguous math.

## Decision

Keep `calculation_events` as a required trace field whenever `actions` includes `calculate`. This preserves the architecture split: the agent decides when math matters, and the CLI makes the math auditable.
