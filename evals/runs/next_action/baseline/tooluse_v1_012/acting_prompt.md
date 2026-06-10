# Next-Action Eval Acting Prompt

You are the acting agent for a Money Model Advisor next-action eval case.

Use the money-model-advisor skill and local CLI. Choose the next action naturally from the case context. Do not ask for expected labels; they are intentionally hidden.

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/next_action/baseline/tooluse_v1_012/business_dir`

Allowed CLI surface:

- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir <business_dir>`
- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot set --business-dir <business_dir> ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir <business_dir> --full`
- `PYTHONPATH=src python3 -m money_model_architect.cli calculate ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli diagnose --snapshot ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli search ...`
- `PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir <business_dir> --message ...`

Visible case context:

```json
{
  "case_id": "tooluse_v1_012",
  "conversation_context": "The user asks a simple business vocabulary question that does not require saved business state, local business docs, or Money Models corpus search.",
  "scenario_id": "1584_design",
  "user_turn": "what does CAC stand for?"
}
```

After acting, record observable steps for `complete`. Do not infer actions from the hidden label.
