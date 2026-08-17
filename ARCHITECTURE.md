# Architecture

**Updated:** 2026-08-14

This is the technical reference for the local Money Model Advisor. `DESIGN.md`
explains why the choices were made; `GOLDEN_DATASET.md` maps the evidence.

## Runtime

```text
human talks to agent
→ agent follows the Money Model Advisor skill
→ agent starts a CLI-backed session and reads saved business context
→ agent chooses whether to clarify, calculate, inspect, search, or answer
→ CLI executes deterministic work and returns structured evidence
→ agent writes the answer
→ CLI validates and records the completed turn
```

The agent owns semantic judgment. The CLI owns deterministic execution,
persistence, and validation. Deterministic chat synthesis is not the advisor
brain.

## Components

| Responsibility | Implementation |
|---|---|
| Agent operating contract | `.codex/skills/money-model-advisor/SKILL.md` |
| Business context and paths | `src/money_model_architect/business_context.py` |
| Snapshot schema and persistence | `src/money_model_architect/snapshot.py` |
| Deterministic formulas | `src/money_model_architect/calculator.py` |
| Diagnostic helpers | `src/money_model_architect/diagnose.py` |
| Query request validation | `src/money_model_architect/advisor_queries.py` |
| Chunking and lexical retrieval | `src/money_model_architect/retrieval.py` |
| Embeddings and cache | `src/money_model_architect/embeddings.py` |
| Local and Pinecone vector stores | `src/money_model_architect/vector_store.py` |
| Retrieval execution and evidence | `src/money_model_architect/advisor_retrieval.py` |
| CLI surface and turn validation | `src/money_model_architect/cli.py` |

## State

`BusinessSnapshot` is the durable cache for accepted business facts. It stores
the business and customer context, current money-model stack, unit economics,
goals and symptoms, calculated fields, readiness, and provenance for accepted
facts.

Updates are explicit. The agent resolves ambiguity before writing; `snapshot
set` replaces the accepted value and provenance; calculated fields recompute.
File paths and hashes record provenance but do not automatically invalidate
facts.

## Search request

When source evidence is needed, the agent writes one `SearchRequest`:

```json
{
  "query": "source-specific query using the question, relevant saved facts, and corpus guide",
  "retrieval_mode": "hybrid"
}
```

The CLI validates the request, executes that exact query, and records the query
and inspected chunks. It does not infer subjects, create query variants, or apply
a request-time metadata filter.

## Retrieval

The active retrieval path is:

```text
one corpus-guided query
→ BM25 candidates + vector candidates
→ reciprocal-rank fusion
→ top five framework-aware chunks
```

- Chunking: `framework-aware`.
- Embeddings: `text-embedding-3-large`, 1,536 dimensions.
- Storage: local in-memory vectors for fast evaluation; Pinecone behind the same
  vector-store boundary for hosted replay.
- Layout: one unfiltered namespace.
- Control: BM25 remains available as the lexical baseline.

Embeddings are deterministic infrastructure calls and are cached under
`.cache/embeddings/`. Agent planning, relevance labeling, and answer synthesis do
not use external model APIs.

## Guardrails

`session finish` validates the recorded artifact before persistence:

- calculation events must use supported formulas and match recomputed results;
- source events must contain the executed query and inspected chunks;
- cited chunk IDs must appear in the recorded inspected set;
- completed answers and semantic audits are bound by content hashes where used.

Citation validation proves provenance, not semantic support. Semantic support is
checked separately by the answer-quality audit and remains an agent judgment.

## Observability

Saved turns and eval artifacts expose:

- actions and calculation events;
- search requests, retrieval mode, inspected chunks, and citations;
- query/retrieval quality metrics;
- p50 and p95 retrieval latency;
- embedding cache hits, misses, and estimated embedding cost;
- model-decision accuracy and latency in the focused routing evaluation.

`python3 scripts/regression_gate.py` collects the stable offline tests, trace
scorers, answer audit, and narrative evidence check behind one fail-fast command.
