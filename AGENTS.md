# Money Model Advisor Agent Instructions

Use this repo as a local, subscription-operated Money Models advisor.

## Default User Flow

The user should be able to give a natural-language request such as:

```text
Use ../1584-design as the business directory and tell me what to fix first.
```

When the user names a business directory, treat that directory as the source of business context and the place where advisor state should be saved.

## Required Workflow

1. Resolve the named business directory.
2. Initialize or refresh local advisor state:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli setup --business-dir /path/to/business
   ```

3. Inspect the saved snapshot:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir /path/to/business
   ```

4. If the snapshot is missing required context, ask the user for the next useful missing fact in plain English. Do not ask them to paste JSON.
5. If the user provided enough context in the request, or the snapshot already has enough context, run one advisor turn:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli chat --business-dir /path/to/business --message "the user's request"
   ```

6. Return the advisor answer in plain English. If useful, mention that state and logs were saved under:

   ```text
   /path/to/business/.money-model-advisor/
   ```

7. Use logs only when you need to inspect prior turns:

   ```bash
   PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir /path/to/business
   ```

## Operating Rules

- Use `ADVISOR_OPERATING_GUIDE.md` for the detailed advisor workflow.
- Use `BusinessSnapshot` as the cached business context.
- Save clear user-provided facts back to the snapshot with `snapshot set`.
- Use deterministic calculations for payback, CAC, gross profit, gross margin, LTGP, and CFA level.
- Use `search` when the answer needs Money Models source support.
- Cite inspected source chunks inline, such as `[payback-period:0]`.
- Do not use provider-key model calls.
- Do not use shallow keyword routing as the advisor brain.
- Do not reread all business files every turn; use the saved snapshot after setup.
