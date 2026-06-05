# BusinessSnapshot v1

`BusinessSnapshot` is the advisor's structured working state for one business.

V1 is intentionally lean. It stores only the information needed to:

1. decide what the advisor should do next;
2. run deterministic unit-economics calculations;
3. diagnose money-model constraints;
4. choose the right Money Models corpus layer;
5. form better retrieval queries;
6. explain what is missing before making a recommendation.

It is not a CRM profile.

## Schema

```json
{
  "schema_version": "business_snapshot.v1",
  "business": {
    "business_type": null,
    "icp": null,
    "delivery_model": null
  },
  "money_model": {
    "attraction_offer": {
      "exists": null,
      "description": null,
      "price": null
    },
    "core_offer": {
      "exists": null,
      "description": null,
      "price": null
    },
    "upsell": {
      "exists": null,
      "description": null,
      "price": null
    },
    "downsell": {
      "exists": null,
      "description": null,
      "price": null
    },
    "continuity": {
      "exists": null,
      "description": null,
      "price": null
    }
  },
  "economics": {
    "cac": null,
    "first_30_day_gross_profit": null,
    "monthly_recurring_gross_profit": null,
    "gross_margin": null,
    "lifetime_gross_profit": null,
    "payback_period_months": null
  },
  "problem": {
    "user_goal": null,
    "reported_symptoms": [],
    "diagnosed_constraints": []
  },
  "advisor_state": {
    "advisory_status": "insufficient_context",
    "missing_fields": [],
    "ready_for_payback_diagnosis": false,
    "ready_for_offer_stack_diagnosis": false,
    "likely_retrieval_layers": [],
    "retrieval_query_terms": []
  },
  "field_sources": {}
}
```

## Field Rules

| Field | Why it is in v1 |
|---|---|
| `business.business_type` | Helps interpret examples and avoid generic advice. |
| `business.icp` | Affects offer design and whether frameworks/examples are relevant. |
| `business.delivery_model` | Helps interpret fulfillment cost, gross margin, and continuity fit. |
| `money_model.attraction_offer` | Maps to acquisition-side framework retrieval. |
| `money_model.core_offer` | Main sale being diagnosed; required for most useful advice. |
| `money_model.upsell` | Helps diagnose payback and backend monetization. |
| `money_model.downsell` | Helps diagnose refunds, payment resistance, and salvage paths. |
| `money_model.continuity` | Helps diagnose LTGP, retention, and cash-flow improvement options. |
| `economics.cac` | Primary acquisition cost input. |
| `economics.first_30_day_gross_profit` | Primary cash-payback input. |
| `economics.monthly_recurring_gross_profit` | Needed when continuity exists or is being designed. |
| `economics.gross_margin` | Distinguishes revenue problems from margin problems. |
| `economics.lifetime_gross_profit` | Needed for LTGP:CAC and long-term economics. |
| `economics.payback_period_months` | Derived metric used for cash-flow diagnosis. |
| `problem.user_goal` | Keeps the advisor from optimizing the wrong thing. |
| `problem.reported_symptoms` | Preserves user language like "cash is tight" or "ads are slow." |
| `problem.diagnosed_constraints` | Stores advisor conclusions like `slow_payback` or `weak_backend`. |
| `advisor_state.advisory_status` | Summarizes the advisory situation without mixing in retrieval progress. |
| `advisor_state.missing_fields` | Drives targeted clarification. |
| `advisor_state.ready_for_payback_diagnosis` | Implementation helper for payback readiness. |
| `advisor_state.ready_for_offer_stack_diagnosis` | Implementation helper for stack-readiness. |
| `advisor_state.likely_retrieval_layers` | Directly supports namespace selection. |
| `advisor_state.retrieval_query_terms` | Directly supports retrieval query construction. |
| `field_sources` | Lets cached file-derived facts be invalidated by source hash. |

## Stack Position Shape

Each money-model position uses the same lean object:

```json
{
  "exists": null,
  "description": null,
  "price": null
}
```

`exists` is not enough by itself. The advisor needs the description and, where relevant, price to avoid bad recommendations like "add an upsell" when an upsell already exists but is underpriced or badly positioned.

Use `null` when unknown. Use `false` only when the system has evidence that the stack position does not exist.

## Advisory Status

`advisory_status` describes what is true about the business/problem. It does not describe whether retrieval has already run.

V1 values:

| Status | Meaning | Next action |
|---|---|---|
| `insufficient_context` | The snapshot is missing fields needed for responsible diagnosis. | Ask for the next missing field. |
| `diagnosable` | The snapshot has enough fields to run diagnostic calculations/reasoning. | Calculate and diagnose. |
| `diagnosed` | The likely constraint has been identified and stored in `problem.diagnosed_constraints`. | Choose recommendation retrieval intent. |
| `recommendable` | The system has enough diagnosis and stack context to recommend a fix. | Retrieve recommendation evidence and answer. |

Retrieval evidence is stored separately in the session trace, not as an advisory status.

Example session evidence shape:

```json
{
  "evidence": {
    "diagnostic": {
      "query": "CAC first 30 day gross profit payback period CFA",
      "layer": "unit-economics",
      "chunks": []
    },
    "recommendation": {
      "queries": [
        {
          "query": "upsell after first sale improve first 30 day gross profit",
          "layer": "upsells"
        }
      ],
      "chunks": []
    }
  }
}
```

## Readiness Rules

The schema is the full lean v1. Readiness flags are separate checks inside that schema.

### Payback Diagnosis

`ready_for_payback_diagnosis` should be true when all of these are known:

- `problem.user_goal`
- `business.business_type`
- `money_model.core_offer.description`
- `economics.cac`
- `economics.first_30_day_gross_profit`

Useful but not required:

- `money_model.core_offer.price`
- `economics.gross_margin`
- `economics.lifetime_gross_profit`
- `economics.monthly_recurring_gross_profit`

If `cac` or `first_30_day_gross_profit` is missing, the advisor should usually ask for that before diagnosing payback or cash constraints.

### Offer Stack Diagnosis

`ready_for_offer_stack_diagnosis` should be true when all of these are known:

- `problem.user_goal`
- `business.business_type`
- `business.icp`
- `money_model.core_offer.description`
- `money_model.attraction_offer.exists`
- `money_model.upsell.exists`
- `money_model.downsell.exists`
- `money_model.continuity.exists`

Descriptions and prices for existing stack positions improve advice, but the first readiness gate only needs to know what exists.

## Persistence

For a business directory at `/company`, store advisor state under:

```text
/company
  .money-model-advisor/
    context_manifest.json
    business_snapshot.json
    embeddings.sqlite3
    sessions/
      2026-06-05T120000Z.json
```

Recommended file roles:

- `context_manifest.json` — optional setup files, file hashes, mtimes, parse status, and errors.
- `business_snapshot.json` — current merged snapshot.
- `embeddings.sqlite3` — cached embeddings for business-context snippets and retrieval queries.
- `sessions/*.json` — message history, tool calls, retrieved chunks, calculations, answer, and final snapshot.

## Cache Rules

`BusinessSnapshot` is the main cache for accepted business facts.

Setup can inspect optional local files and ask the user for missing information. Chat should use `business_snapshot.json` rather than searching local files on every turn. If the user provides new missing information during chat, the advisor saves that value to `business_snapshot.json` with source metadata.

Cache source-linked facts by source hash, not by time.

If a setup file hash has not changed:

- do not reread it during setup unless explicitly forced;
- do not re-embed unchanged text chunks.

If one file changes:

- preserve accepted snapshot facts, but mark any field whose `source_hash` came from that file as stale until setup/intake confirms or updates it;
- re-embed only changed snippets.

Conversation-derived facts stay valid until overwritten by a later conversation turn or contradicted by higher-confidence file data.

Calculated fields are recomputed whenever their inputs change.

## Field Source Format

Every non-null field can have a source record:

```json
{
  "economics.cac": {
    "source_type": "file",
    "source": "metrics/q1-unit-economics.csv",
    "source_hash": "abc123",
    "confidence": "high",
    "updated_at": "2026-06-05T00:00:00Z"
  },
  "economics.payback_period_months": {
    "source_type": "calculated",
    "inputs": [
      "economics.cac",
      "economics.first_30_day_gross_profit",
      "economics.monthly_recurring_gross_profit"
    ],
    "confidence": "high",
    "updated_at": "2026-06-05T00:00:00Z"
  }
}
```

Source types:

- `file`
- `conversation`
- `calculated`

Source confidence:

- `high` — explicit value found in file, user stated directly, or deterministic calculation.
- `medium` — inferred from nearby context.
- `low` — weak inference that should be confirmed before important advice.

## Merge Rules

When multiple sources provide the same field:

1. prefer explicit file data over inferred file data;
2. prefer direct user statements over weak file inferences;
3. prefer newer direct user statements over older direct user statements;
4. recompute calculated fields from the current merged inputs;
5. preserve conflicts in the session trace instead of silently discarding them.

## What v1 Excludes

- company name
- address
- team members
- CRM/contact data
- revenue history beyond the specific economics fields above
- brand voice
- marketing calendar
- channel-by-channel attribution
- external integrations

Those may be useful in other products. They are not needed for v1 diagnosis or retrieval targeting.
