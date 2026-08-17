# Open Items

**Updated:** 2026-08-17

This is the short completion checklist. `REMEDIATION_PLAN.md` contains the
detailed acceptance record; completed experiments should not be reopened here.

## Most recently completed

- Expanded semantic answer quality from six source-event cases to 20 balanced
  full-answer cases across five business contexts.
- The 16/20 frozen baseline exposed a shared input-sufficiency failure in
  clarification answers. A general runtime and advisor-rule correction—not
  case-specific answer patches—brought fresh runs to 20/20 with 22/22 material
  claims supported. The full unit suite and relevant evaluations pass.
- Every quantitative evidence block in the narrative now has a default-closed,
  human-readable case table with filtering, sorting, and expandable row details.
  Canonical raw files and reports remain directly linked.
- `python3 scripts/regression_gate.py` now runs the stable offline checks behind one
  fail-fast command. Strict scorer modes reject missing or failed saved results; the
  gate does not call acting models or hosted services.

## Required for portfolio completion

1. **Final narrative review.** Read the rendered HTML from beginning to end,
   verify its numbers against canonical reports, and remove remaining stale or
   unnecessary language.

## Deferred until the runtime exposes the needed evidence

- **Comparable billed agent cost.** The current agent runs through a subscription
  harness. Add per-case billed cost only when the deployment path uses metered
  model calls.

## Optional extensions, not completion blockers

- A thin TypeScript/API or hosted user interface over the existing Python core.
- A new same-harness provider comparison if comparable provider access becomes
  available.
- A learned reranker if future cases show useful candidates entering the pool but
  regularly missing the returned top five.
- Namespace partitioning if corpus growth creates measurable retrieval
  interference.

## Decisions already settled

- The operating agent is `gpt-5.5`; `gpt-5.4-mini` is a validated bounded
  query-writer option but did not replace the operating agent.
- The active query is one corpus-guided, unfiltered query.
- Retrieval is hybrid over framework-aware chunks.
- `text-embedding-3-large` at 1,536 dimensions is the selected embedding setup.
- Pinecone is behind the retrieval boundary; the local backend remains the fast
  regression baseline.
- One unfiltered namespace remains the active layout because the tested split did
  not improve quality.
