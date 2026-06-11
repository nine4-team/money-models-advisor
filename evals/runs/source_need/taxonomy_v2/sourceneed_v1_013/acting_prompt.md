# Source-Need Generation Acting Prompt

You are the acting agent for a Money Model Advisor source-need generation eval case.

Use the money-model-advisor skill and local CLI as needed. Expected labels are intentionally hidden.

Task: decide whether Money Models source-material search is needed for the current turn. If search is needed, generate a structured source need with `intent`, `layers`, and `focus_terms`. If search is not needed, set source need to null.

Do not use source-material search as a substitute for missing business facts. If the current turn asks for a business recommendation that depends on missing economics, offer-stack facts, prior-session context, or deterministic math before an answer can be responsibly given, choose no source search for this step.

Do use source-material search when the snapshot or prior-session context already contains enough facts for a source-backed explanation, diagnosis, comparison, or recommendation. A missing optional field should not block search when the user is asking for conceptual source support.

Do not search for simple vocabulary answers that can be answered directly without citation. Source search is for source-backed advisory claims, not every definition.

Keep layers minimal. Include only the corpus layers needed to support the source-backed claim; extra layers reduce precision.

Choose intent by retrieval job, not by the mood of the final answer:

- `teaching_evidence`: explain a Money Models concept or framework.
- `diagnostic_evidence`: support interpretation of known business economics or constraints.
- `comparison_evidence`: compare two concepts, options, or layers.
- `recommendation_evidence`: source support for a concrete next move after enough business facts are known.

Choose layers by the mechanism the source material must support:

- front-end attraction offer -> `offers`
- post-sale add-on or premium next offer -> `upsells`
- payment plan, pay-less-now option, or friction-reducing alternative -> `downsells`
- recurring maintenance, membership, or repeat post-purchase service -> `continuity`
- CAC, gross profit, payback, or acquisition capacity interpretation -> `unit-economics`

Use payback or CAC as focus terms without adding `unit-economics` when the source claim is about a concrete fix mechanism such as continuity or upsells.

Allowed intents:

- `teaching_evidence`
- `diagnostic_evidence`
- `comparison_evidence`
- `recommendation_evidence`

Allowed layers:

- `unit-economics`
- `offers`
- `upsells`
- `downsells`
- `continuity`

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/source_need/taxonomy_v2/sourceneed_v1_013/business`

Visible case context:

```json
{
  "case_id": "sourceneed_v1_013",
  "conversation_context": "The snapshot is empty. The user asks a simple business vocabulary question.",
  "scenario_id": "1584_design",
  "user_turn": "what does gross profit mean in plain English?"
}
```

After acting, complete the trace with `scripts/capture_source_need_trace.py complete ...`. Do not look up expected labels.
