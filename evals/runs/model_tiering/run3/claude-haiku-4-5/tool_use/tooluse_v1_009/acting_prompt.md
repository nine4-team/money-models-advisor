# Next-Action Eval Acting Prompt

You are the acting agent for a Money Model Advisor next-action eval case.

Consult the money-model-advisor skill, then use the local CLI to act. The skill is the authoritative rulebook and its rules decide the close calls. Choose the next action naturally from the case context. Do not ask for expected labels; they are intentionally hidden.

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_tiering/run3/claude-haiku-4-5/tool_use/tooluse_v1_009/business_dir`

Allowed CLI surface:

- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir <business_dir>`
- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot set --business-dir <business_dir> ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir <business_dir> --full`
- `PYTHONPATH=src python3 -m money_model_architect.cli calculate ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli diagnose --snapshot ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli search --business-dir <business_dir> --source-need-json ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli search "raw debug query" --layer <layer>`
- `PYTHONPATH=src python3 -m money_model_architect.cli turn record --business-dir <business_dir> --user-message ... --assistant-message ...`

Visible case context:

```json
{
  "case_id": "tooluse_v1_009",
  "conversation_context": "The user asks for a conceptual explanation about fulfillment cost and CAC payback.",
  "scenario_id": "1584_design",
  "user_turn": "why do we need fulfillment cost to understand whether ads can work?"
}
```

After acting, record observable steps for `complete`. Do not infer actions from the hidden label.

## Noninteractive Eval Requirement

Before your final response, you must create `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_tiering/run3/claude-haiku-4-5/tool_use/tooluse_v1_009/run.json` by running:

```bash
PYTHONPATH=src python3 scripts/capture_tool_use_trace.py complete /Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_tiering/run3/claude-haiku-4-5/tool_use/tooluse_v1_009 --workflow-steps '<json-array>' --session-paths '<json-array>' --actual-actions '<json-array>' --final-answer '<brief answer or action summary>'
```

Use the local CLI where the case calls for it. Do not look up expected labels.
