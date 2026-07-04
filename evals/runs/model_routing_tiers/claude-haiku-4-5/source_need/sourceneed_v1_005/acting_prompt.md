# Source-Need Generation Acting Prompt

You are the acting agent for a Money Model Advisor source-need generation eval case.

Consult the money-model-advisor skill before you decide, then use the local CLI to act. The skill is the authoritative rulebook for the search decision, intents, and layers; where a case is a close call, its rules decide it, including the rule that a unit-economics search stays `diagnostic_evidence` even when the final answer contains a recommendation. This prompt only summarizes the skill. Expected labels are intentionally hidden.

Task: decide whether Money Models source-material search is needed for the current turn. If search is needed, generate a structured source need with `intent`, `layers`, and `focus_terms`. If search is not needed, set source need to null.

Apply the decision rules below exactly. They are inlined verbatim from the
authoritative rulebook (`source_need_rules.md`); this is the same file the operating
skill points to, so there is one source of truth.

# Source-Need Decision Rules

Single source of truth for deciding whether to run a source-material search and how
to structure the source need. The operating skill and the eval acting prompts both
pull these rules from this file. Do not restate them anywhere else — change them here.

## When to search

- Search source material when the answer needs Money Models support for a concept,
  comparison, diagnosis, or recommendation, and the snapshot or prior-session context
  already holds enough business facts to make a source-backed claim.
- Do not use source search as a substitute for missing business facts. If the
  responsible next move is to get CAC, gross profit, fulfillment cost, current offer
  details, or prior-session context first, do that instead and do not search this step.
- Do not search for simple vocabulary answers that can be answered without a citation.
- A missing optional field should not block search when the user is asking for
  conceptual source support.

## Layers (these drive retrieval — choose carefully)

Choose layers by the mechanism the source material must support:

- front-end attraction offer -> `offers`
- post-sale add-on or premium next offer -> `upsells`
- payment plan, pay-less-now option, or friction-reducing alternative -> `downsells`
- recurring maintenance, membership, or repeat post-purchase service -> `continuity`
- CAC, gross profit, payback, or acquisition-capacity interpretation -> `unit-economics`

Keep layers minimal; extra layers make retrieval noisier. Use payback or CAC as focus
terms without adding `unit-economics` when the source claim is about a concrete fix
mechanism such as continuity or upsells.

## One retrieval job per search (this drives layer and focus-term choice)

- Generate one source need per search. If an answer needs two retrieval jobs, run two
  searches with two source needs instead of mixing them into one.
- Boundary rule: a search that interprets the business's economics stays on
  `unit-economics` even when the final answer contains a recommendation. If the source
  is justifying why the economics point a certain way, keep it a `unit-economics`
  search; then run a separate search on the concrete fix layer (`offers`, `upsells`,
  `continuity`, `downsells`) for the recommended move.
- Do not add a `unit-economics` search merely because known economics appear in the
  answer. If the frame is already established and the user asks for a concrete fix,
  search only for the fix mechanism unless the answer makes a fresh source-backed
  economics claim.

## Focus terms and query variants

- `focus_terms`: the specific evidence the search must surface.
- `query_variants`: 2-4 short, source-facing search phrasings authored for the claim in
  the current turn. Three is the normal target; four is the cap. If you need more than
  four, split the answer into narrower source needs. Do not rely on the deterministic
  fallback query except for debugging.

## Intent (recorded annotation, not scored)

Record the retrieval job as `intent` for traceability. Intent does not change retrieval
— `layers`, `focus_terms`, and `query_variants` do — and it is not graded, so choose the
closest fit and move on:

- `teaching_evidence`: explain a Money Models concept or framework.
- `diagnostic_evidence`: support interpretation of known business economics or constraints.
- `comparison_evidence`: compare two concepts, options, or layers.
- `recommendation_evidence`: support a concrete next move after enough business facts are known.

Allowed intents: `teaching_evidence`, `diagnostic_evidence`, `comparison_evidence`, `recommendation_evidence`.
Allowed layers: `unit-economics`, `offers`, `upsells`, `downsells`, `continuity`.

Business dir: `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_routing_tiers/claude-haiku-4-5/source_need/sourceneed_v1_005/business`

Visible case context:

```json
{
  "case_id": "sourceneed_v1_005",
  "conversation_context": "The snapshot has a draft diagnostic front-end offer. The user asks what should come next to improve first-month profit.",
  "focus_aliases": {
    "first sale": [
      "diagnostic offer"
    ],
    "maximize 30 day profits": [
      "first-month profit",
      "first 30 day gross profit"
    ],
    "next offer": [
      "pre-designed room packages"
    ],
    "upsell after first sale": [
      "post-sale upsell",
      "post-sale add-on"
    ]
  },
  "scenario_id": "1584_design",
  "user_turn": "if the diagnostic sells, what should we offer next to increase first-month profit?"
}
```

After acting, complete the trace with `scripts/capture_source_need_trace.py complete ...`. Do not look up expected labels.

## Noninteractive Eval Requirement

Before your final response, you must create `/Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_routing_tiers/claude-haiku-4-5/source_need/sourceneed_v1_005/run.json` by running:

```bash
PYTHONPATH=src python3 scripts/capture_source_need_trace.py complete /Users/benjaminmackenzie/Dev/money-model-architect/evals/runs/model_routing_tiers/claude-haiku-4-5/source_need/sourceneed_v1_005 --source-search-decision <true|false> --source-need '<json-if-true>' --notes '<brief rationale>'
```

Your final response should only summarize the recorded decision.
