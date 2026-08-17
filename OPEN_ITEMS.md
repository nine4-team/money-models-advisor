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

1. **Correct the workflow diagram.** Separate inspect-within-the-turn from
   clarification, which ends the turn until the user supplies the missing context.
2. **Complete the evaluation explanation.** Extend the framework and scoring text to
   cover search decisions, calculation traces, answer quality, and the stable
   regression gate.
3. **Make the remaining retrieval decisions explicit.** State the selected embedding
   setup and include the measured before/after Pinecone latency improvement.
4. **Reconcile supporting documents.** Remove the false claim that intermediate
   answer-quality scratch runs are preserved, close the stale query-model-selection
   language, and replace the outdated six-answer description.
5. **Complete the final visual review.** Quantitative claims match the canonical
   reports. The remaining rendered-layout check is manual because automated
   inspection of this local `file://` page is blocked by browser security policy.

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
