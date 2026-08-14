# Open Items

**Updated:** 2026-08-14

This is the short completion checklist. `REMEDIATION_PLAN.md` contains the
detailed acceptance record; completed experiments should not be reopened here.

## Required for portfolio completion

1. **Broaden end-to-end answer quality.** Add genuinely different business
   contexts or observed failures to the six-case seed answer audit. Do not create
   more cases by lightly paraphrasing the existing ones.
2. **Add one regression gate.** Provide one command or CI job that runs the stable
   local tests and scorers and fails on a real regression.
3. **Final narrative review.** Read the rendered HTML from beginning to end,
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
