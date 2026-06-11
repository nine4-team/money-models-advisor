# Tooling Shortlist

Current recommendation for the next build pass: keep the product agent-first and CLI-backed, use setup/intake to build a `BusinessSnapshot`, and add Pinecone behind a retrieval storage boundary. The local backend remains the fast eval baseline; Pinecone demonstrates the hosted retrieval path. A web UI should come after the shared advisor/retrieval core is clean enough to reuse.

## Recommended stack

| Need | Recommended tool | Why it helps this project | Source |
|---|---|---|---|
| Stateful advisor orchestration | Simple CLI state loop first; LangGraph only if the loop earns it | The product is multi-turn, but the v1 should prove the state and tool boundaries before adding orchestration machinery. | Local architecture decision |
| Local agent/operator workflow | Codex environment | The human talks to an agent; the agent follows the project skill's guidance and runs local CLI tools. Treat this as the v1 advisor runtime. | Local architecture decision |
| Setup/intake input | Plain local directory + Markdown/JSON/YAML readers | Optional setup input can come from local notes, offers, metrics, docs, and prior sessions. Runtime chat should use the saved snapshot. | Local architecture decision |
| Local session and snapshot store | JSON now; SQLite later only if traces become unwieldy | JSON files are enough for `BusinessSnapshot`, context manifests, and sessions in v1. | Local implementation |
| Local retrieval baseline | Standard-library BM25-style search plus local cached embeddings | Keeps the advisor runnable and testable without hosted infrastructure. | Local implementation |
| Hosted vector storage | Pinecone | Demonstrates the production RAG storage layer named in the target job family while keeping retrieval behavior behind an adapter. | Local architecture decision |
| Eval and trace visibility | Arize Phoenix | Open-source observability/evaluation tool for LLM apps; useful once the CLI has multi-step traces that are hard to inspect by logs alone. | https://arize.com/docs/phoenix/, https://github.com/Arize-ai/phoenix |
| Future web/chat UI | Vercel AI SDK + assistant-ui | Only after the CLI loop works. Vercel AI SDK handles streaming/tool calls; assistant-ui provides React chat components that work with Vercel AI SDK. | https://vercel.com/docs/agents, https://github.com/assistant-ui/assistant-ui |

## Do not build yet

- A full web app before the shared advisor/retrieval core works through both local and Pinecone-backed retrieval.
- Multi-agent orchestration beyond a simple state graph.
- A brittle regex diagnostic router as the production brain.
- A custom chat UI from scratch.
- External model-service calls for agent planning, labeling, answer synthesis, or acting-agent eval work.
- External-service-dependent labeling.

## Immediate shortcut

Build the next slice as:

```bash
money-model-advisor setup --business-dir /path/to/company
money-model-advisor snapshot --business-dir /path/to/company
money-model-advisor search --business-dir /path/to/company --source-need-json ...
money-model-advisor turn record --business-dir /path/to/company ...
```

Setup should:

1. create `.money-model-advisor/`;
2. record optional local files in `context_manifest.json`;
3. collect the fields needed for `BusinessSnapshot`;
4. write accepted facts to `business_snapshot.json`.

The agent-operated turn should:

1. load `business_snapshot.json`;
2. ask targeted missing-context questions when needed;
3. save any new user-provided facts back to the snapshot;
4. run deterministic economics when fields are present;
5. search source material from the Money Models corpus when the advisor needs citations;
6. write session traces back to `.money-model-advisor/`.
