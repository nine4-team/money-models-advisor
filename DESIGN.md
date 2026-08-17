# Building a Money Model Advisor

**Updated:** 2026-08-14

This is the canonical design for the current product. `ARCHITECTURE.md` gives the
technical map, `GOLDEN_DATASET.md` maps the evaluations, and historical experiment
details remain in `evals/reports/`.

## Product

The product is an agent-operated advisor for Alex Hormozi's *$100M Money Models*.
It helps a founder establish business context, calculate unit economics, retrieve
relevant source material, and decide what to change next.

The user talks to an agent. The agent follows the project skill and uses the local
CLI. The CLI does not synthesize the advice.

## Responsibility boundary

The agent owns semantic judgment:

- choose whether to clarify, inspect business context, calculate, search, or answer;
- decide which saved facts matter to the current question;
- write one corpus-guided search query;
- decide whether returned passages are useful;
- compose and support the final answer.

The CLI owns deterministic work:

- persist the `BusinessSnapshot` and completed turns;
- calculate supported metrics;
- execute lexical and vector retrieval;
- reuse cached embeddings;
- validate request and trace structure;
- generate reproducible evaluation artifacts.

This boundary keeps semantic behavior testable without hiding a second advisor in
deterministic routing code.

## Workflow

```text
user question
→ session start loads snapshot, recent turns, and available operations
→ agent chooses the next action
→ if context is missing, inspect or clarify and save accepted facts
→ if math is needed, use the deterministic calculator
→ if source support is needed, write and run one SearchRequest
→ inspect returned passages and write the answer
→ session finish validates and records the turn
```

Search is one possible action, not the default action for every turn. The search
gate and the query/retrieval pipeline are therefore evaluated separately.

## Memory

`BusinessSnapshot` stores accepted facts, calculated economics, advisory state,
and provenance for accepted facts. The agent resolves conflicts before updating
the snapshot; the CLI performs the explicit write and recomputes dependent fields.
There is no hidden source-priority merge engine.

Local business documents are inputs the agent may inspect when needed. They are
not part of the Money Models retrieval corpus.

## Knowledge and retrieval

The source corpus contains 32 lesson transcripts. The selected retrieval path is:

1. The agent writes one query from the current question, relevant saved business
   facts, and the versioned corpus guide.
2. The CLI runs the query without a metadata filter.
3. BM25 and vector rankings are fused with reciprocal-rank fusion.
4. The agent receives the top five framework-aware chunks with citation IDs.

The runtime choices are:

| Decision | Selected approach | Evidence |
|---|---|---|
| Query generation | Corpus-guided single rewrite | Leads raw-question and unguided controls under both tested query writers and retrievers on 46 cases. |
| Chunking | Framework-aware | Preserved 100% Hit@5, improved Useful@5 over heading-aware, and reduced oversized chunks. |
| Retriever | Hybrid | Improved Useful@5 over BM25 for both guided writers while preserving 100% Hit@5. |
| Embedding | `text-embedding-3-large`, 1,536 dimensions | Improved local Useful@5 from 78.7% to 86.5% over Small. |
| Vector storage | Pinecone behind a storage boundary | Hosted replay reached 86.1% Useful@5 at 1.13s p50 and 1.43s p95. |
| Namespace layout | One unfiltered namespace | Five subject namespaces did not improve retrieval quality. |
| Query-writer model | `gpt-5.5` in the operating turn | Mini is viable for bounded writing, but a separate call has no measured end-to-end benefit. |

BM25 remains the lexical control. The local vector backend remains the fast
evaluation baseline. Retired retrieval experiments are preserved under `archive/`.

## Model routing

The operating agent remains `gpt-5.5`. On the balanced 48-case search-decision
suite it found all 24 required searches and avoided all 24 prohibited searches.
`gpt-5.4-mini` scored 47/48, with one audited false negative and no false
positives. Mini remains a validated bounded query-writer option because it found
useful evidence within five hybrid results on all 46 retrieval cases.

The project does not claim a metered cost saving from this comparison. Agent
execution uses a subscription harness, so comparable billed agent cost is not
available.

## Guardrails and traces

The CLI validates evidence that can be checked deterministically:

- calculation events are recomputed and rejected when invalid or mismatched;
- search events preserve the authored and executed query plus inspected chunks;
- citations must refer to chunks in the recorded inspected set;
- completed artifacts must satisfy the trace schema.

These checks prove calculation integrity and citation provenance. The agent remains
responsible for whether a passage actually supports a claim. A separate 20-answer
semantic audit across five business contexts currently verifies 22 material claims.

## Evaluation strategy

Each dataset isolates a product risk:

- 48 cases test the search/no-search decision;
- 46 cases test query generation and retrieval;
- 6 cases test current source-event behavior;
- 5 cases test calculation traces;
- 20 current-path answers test usefulness, correctness, restraint, and semantic support.

Returned retrieval passages were reviewed for missed useful results and overly
broad labels before final scoring. Codex performed the semantic passage and answer
audits; no independent human-review claim is made.

## Remaining work

The core design decisions are settled, and the stable offline checks run through
`python3 scripts/regression_gate.py`. Completion work is limited to a final rendered
narrative review. New infrastructure should be added only when new evidence exposes
a product risk that the current design does not handle.
