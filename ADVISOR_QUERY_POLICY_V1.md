# Advisor Query Policy v1

This document summarizes the active source-search contract. The executable operating
rules live in `.codex/skills/money-model-advisor/search_request_rules.md`; the CLI
contract lives in `CLI_DESIGN.md`.

## Decision sequence

1. The agent decides whether the answer needs Money Models source support.
2. If relevant business facts are missing, the agent obtains them before searching.
3. For each distinct evidence job, the agent writes one corpus-guided query.
4. The CLI executes that query through unfiltered hybrid retrieval and records the
   request, exact executed query, and returned chunks.

Search is appropriate when the answer needs source support for a concept, comparison,
diagnosis, or recommendation. It is not a substitute for reading saved state,
inspecting a business document, calculating known numbers, or asking for missing
context.

## Query inputs

The query writer receives only:

- the current user question;
- relevant accepted facts from the saved `BusinessSnapshot`; and
- `evals/query_generation/corpus_guide_v1.json`.

The corpus guide combines book vocabulary and frameworks. It is a translation aid,
not a checklist. The query should preserve the complete information need and add
business context only when that context changes or disambiguates the requested
evidence.

## Request shape

```json
{
  "intent": "recommendation_evidence",
  "user_turn": "What should I add after the initial sale?",
  "query": "upsell sequence after initial sale increase first 30 day gross profit"
}
```

- `query` is the one text query the CLI executes.
- `user_turn` preserves the original question in the trace.
- `intent` is an audit label. It does not alter retrieval.

If the answer needs two genuinely different evidence jobs, the agent may issue two
separate requests. Each request still contains one query.

## Retrieval contract

The active path uses:

- framework-aware chunks;
- BM25 plus vector retrieval;
- reciprocal-rank fusion;
- `text-embedding-3-large` at 1,536 dimensions;
- one Pinecone namespace with no subject filter; and
- a top-five returned context.

BM25 remains the lexical control in evaluation. The local vector store remains the
fast evaluation backend.

## Retired compatibility path

`SourceNeed`, subject routing, query variants, deterministic fallback queries, and
namespace filters remain in code only to reproduce older experiments and traces. They
do not define product behavior and should not be used by the advisor skill.
