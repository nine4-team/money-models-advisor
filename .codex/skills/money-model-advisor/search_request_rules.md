# Runtime Search-Request Rules

These rules govern the active query-generation and retrieval path. The retired
filtered and multi-query rulebook is preserved under
`archive/source-need-experiment/`; it is not the runtime query contract.

## When to search

- Search when the answer needs Money Models support for a concept, comparison,
  diagnosis, or recommendation and the snapshot already holds enough relevant facts.
- Do not search instead of obtaining missing business facts or prior-session context.
- For a yes/no acquisition-scale question with missing CAC or gross-profit inputs,
  clarify without searching. The corpus cannot supply the business's numbers. Search
  only if the human separately asks for a Money Models explanation of why those inputs
  matter or if enough business facts exist to make a source-backed recommendation.
- Do not search for a simple vocabulary answer that does not need a citation.

## One evidence job per search

- Generate one search request per evidence job. If an answer needs two genuinely
  different kinds of evidence, run two searches instead of mixing them into one query.
- Do not rerun an economics search merely because known economics appear in the answer.

## Generate the query

- Before writing a query, read `../../../evals/query_generation/corpus_guide_v1.json`.
  It is the same versioned guide used by the winning development experiment.
- Use the current user question, the saved BusinessSnapshot, and that guide to write
  one concise source-search query.
- Treat the guide as a translation reference, not a checklist. Translate ordinary
  language into canonical source terminology when that helps retrieval.
- Preserve the full information need. Include every concept needed for the mechanism,
  relationship, comparison, sequence, or combined system being asked about.
- Use business context only when it changes or disambiguates the evidence needed. Do
  not add related concepts simply because the guide lists them nearby.
- Do not answer the question or speculate about the answer inside the query.
- Do not generate variants, a deterministic fallback, a subject filter, or a namespace
  filter. Those approaches were not part of the winning method.

## Active request fields

- `query`: the single corpus-guided query that the CLI executes.
- `user_turn`: the current user message, retained for trace context.
- `intent`: the closest audit label; it does not alter retrieval. Choose one of
  `teaching_evidence`, `diagnostic_evidence`, `comparison_evidence`, or
  `recommendation_evidence`.
