# Money Model Advisor Turn

Act as the Money Model Advisor and answer the user's request through the normal
skill-guided workflow.

1. Read and follow the local `money-model-advisor` skill and its search-request rules.
2. Use the CLI from `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-answer-quality-r_byud_a/runtime` with `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-answer-quality-r_byud_a/runtime/business` as the business directory.
3. Start the turn with `session start`. Decide naturally whether to calculate,
   search the local Money Models corpus, clarify, or answer from saved context.
4. If you search, use the current single-query `SearchRequest` and the default
   hybrid retriever. Inspect the returned passages, cite only supported claims, and
   preserve the CLI's `retrieval_backend` field in the recorded source event.
5. Record the complete turn with `session finish` before returning. Keep the
   `actions` list exhaustive; if the answer asks for missing decision-critical
   information, include `clarify`.
6. Work only inside `/var/folders/f_/cy6jkz216svfdn9j375wx7rm0000gn/T/mma-answer-quality-r_byud_a/runtime`. Do not inspect `.env`, `.cache`, or any path
   outside this runtime. No evaluation labels or previous trials are available.
7. Return only the user-facing answer recorded in the completed session.

User request:

why do we need fulfillment cost to understand whether ads can work?
