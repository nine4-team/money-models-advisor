# Corpus

Source material for the money-model advisor. Everything here is read-only input to the ingest pipeline — never edit in place; re-derive from upstream in `nine4/shared-resources/`.

## Layout

| Path | What it is | Role in the system |
|---|---|---|
| `transcripts/` | 32 chapter transcripts of Hormozi's *$100M Money Models* | Primary RAG corpus — chunked and embedded into Pinecone namespaces |
| `coach/` | Prior coaching artifact: `decision-trees.md`, `diagnostic-flow.md`, `examples.md`, `index.md`, `system-instructions.md` | Reference design for the `diagnose_constraint` and `critique_offer` tools — encodes the decision logic a human coach would use, which the agent should mirror |
| `money-models-frameworks.md` | Hand-distilled summary of all frameworks in the book | Seed for the golden eval set and a sanity check against retrieval — if a framework shows up here it must be retrievable |
| `skill/SKILL.md` + `skill/openai.yaml` | Prior agent skill / config | Reference for tool boundaries, invocation triggers, and the workflow ordering already validated in practice |

## Provenance

Pulled from:
- `nine4/shared-resources/frameworks/hormozi-money-models/transcripts/`
- `nine4/shared-resources/frameworks/hormozi-money-models/coach/`
- `nine4/shared-resources/frameworks/hormozi-money-models/money-models-frameworks.md`
- `nine4/shared-resources/skill-packs/alex-hormozi/money-models/`

## How each piece feeds the architecture

- **Transcripts → namespaces.** The chunker (§4) reads from `transcripts/` and writes to the five Pinecone namespaces defined in §3. Each filename maps to a chapter; metadata preserves that.
- **Coach decision trees → tool design.** `coach/decision-trees.md` and `coach/diagnostic-flow.md` define the branching logic for `diagnose_constraint`. The tool should reproduce this logic, not reinvent it — the LLM picks the branch, the tool returns the structured next step.
- **Coach examples → golden eval set.** `coach/examples.md` contains worked examples. These become the first ~10 entries in `evals/golden.jsonl` with known-correct retrievals and ideal answers.
- **Coach system-instructions → agent system prompt.** Already-validated voice and constraints. Lift the substance, restructure for tool-use loop.
- **Frameworks summary → retrieval sanity check.** The eval framework asserts every named framework in `money-models-frameworks.md` is retrievable by name from the right namespace.
- **SKILL.md → tool surface validation.** Confirms the six-tool design in §8 covers the workflow this skill already encodes (diagnose CAC/GP/payback, map offer layers, find simplest economic improvement).
