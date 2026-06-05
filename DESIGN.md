# Building a Money Model Advisor

How this RAG system was designed, in roughly the order the decisions were made. The style goal is closer to an applied ML paper than a product spec: each major architecture choice has a hypothesis, competing variants, evaluation metrics, and a decision rule.

The product is an advisor for Alex Hormozi's *$100M Money Models*. It diagnoses unit economics, designs offer stacks, critiques existing offers, runs the calculations from the book, compares frameworks, and explains them on demand. Built to mirror the [Senior AI Engineer JD at Acquisition.com](https://jobs.ashbyhq.com/acquisition/9789dd49-c6bd-4672-8cd3-9f67f2dea7c1), which owns the corpus.

This doc is the canonical narrative. It is the one to send someone who wants to understand the modeling decisions and why they were made. [ARCHITECTURE.md](ARCHITECTURE.md) is the line-by-line technical reference and JD-to-file map. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) is the build order. [TOOLING_SHORTLIST.md](TOOLING_SHORTLIST.md) records the practical libraries/tools to shortcut development. `evals/reports/` contains the checked-in evidence tables that support the decisions here.

---

## 0. Corrected product frame

The product is not a one-shot RAG bot. A founder using this advisor will often start with an open-ended goal:

- "Help me build a money model."
- "I think my CAC is high."
- "Our offer works, but cash is tight."
- "What should I add after the first sale?"
- "Here is my funnel; what would Hormozi change?"

Those are not all retrieval questions. They are conversation starts. The system has to determine what kind of advisory session is underway, gather missing context, maintain a structured business snapshot, and only then retrieve the frameworks that support the next recommendation.

The corrected architecture is:

```text
open-ended user message
→ classify conversation mode
→ update structured business snapshot
→ ask for missing context when needed
→ run deterministic calculations/diagnosis when enough data exists
→ retrieve frameworks for the diagnosed/design constraint
→ answer with citations and next action
```

The key state object is the `BusinessSnapshot`: business type, offer, price, CAC, gross profit, gross margin, payback period, sales motion, current stack, constraints, and user goals. Retrieval is downstream of this state. For teach/compare questions, the advisor can retrieve immediately. For diagnose/design/critique sessions, the advisor should usually ask clarifying questions before retrieval.

The first usable product does not need to be a web application. A CLI is a better fit for the current reality: run `money-model-advisor --business-dir /path/to/company-context`, let the tool read local business notes, offers, funnel docs, metrics files, and prior session state, then conduct an advisory conversation in the terminal. That makes the product useful inside a personal workflow, avoids premature UI work, and lets the system use the local Codex/OpenAI runtime during development while preserving a clean provider interface for later deployment.

This reframes the retrieval experiments below. The experiments are still useful, but they are not the whole product design. They show which retrieval policy works once the advisor has a well-formed intent or diagnosed constraint. The real application design is stateful conversation plus tools, not "single query in, answer out."

## 1. Start with the corpus

The first step was getting the source material into a form I could read end-to-end. The course is on acquisition.com as video lessons. I transcribed all 32 lessons into `corpus/transcripts/`, one file per lesson, named for the concept it covers (`rollover-upsell.txt`, `payback-period.txt`, `cfa.txt`).

Reading them back-to-back surfaced two things about how the book is organized.

First, there's an explicit taxonomy running through the whole thing: the money-model offer stack of attraction offer, upsell, downsell, and continuity. Hormozi names these four positions and the rest of the book fills them in.

Second, the unit-economics chapters (CAC, gross profit, payback period, client-financed acquisition) are a different kind of content. They don't belong to any stack position. They're the metrics you use to evaluate whether the stack is working.

Four stack positions plus a diagnostic layer is the structure I designed around.

---

## 2. Write the advisory flow first

Before touching embeddings, I wrote the decision tree a human coach would use to navigate this material. It's in `corpus/coach/decision-trees.md` along with a diagnostic flow, worked examples, and the system instructions for an earlier coaching agent that used the same corpus.

The tree starts at unit economics — "what are your numbers?" — and branches based on which metric is the binding constraint:

- Payback too long → upsells or continuity
- LTGP:CAC too low → gross profit margin and continuity
- No working attraction offer → offer types
- High refund rate → downsell design

Each branch then drills into the specific framework that addresses the constraint.

Writing this before designing the index gave me a spec for how the advisor should update state, decide what information is missing, run calculations, and sequence retrieval. It is an advisory flow, not merely a query-classification tree.

---

## 3. Namespaces

A namespace defines the slice of the corpus that retrieval will search. If that slice matches the advisor's current task, retrieval is clean. If it doesn't, retrieval pulls in unrelated content and the generator has to work harder to ignore it.

The advisory flow from §2 is a description of what the system needs to reason about. Unit economics live at the top of the tree. The four stack positions live at the next level. If the namespaces line up with those nodes, the advisor can retrieve from the slice that matches the diagnosed or designed constraint.

That gives the five Pinecone namespaces:

| Namespace | Chapters |
|---|---|
| `unit-economics` | cac, payback-period, gross-profit, cfa, how-businesses-make-money, context |
| `offers` | attraction-offers, offer-types, decoy-offers, free-giveaways, free-trials, free-with-consumption |
| `upsells` | upsell-offers, classic-upsell, menu-upsell, anchor-upsell, rollover-upsell, buy-x-get-y |
| `downsells` | downsells, feature-downsells, pay-less-now, payment-plans, waived-fee, win-your-money-back |
| `continuity` | continuity-offers, continuity-bonus, continuity-discounts |

A few cross-cutting chapters (`make-your-money-model`, `money-models-offer-stacks`, `ten-years-ten-minutes`, `ride-along-apprenticeship`, `final-words`) get chunked normally and tagged with all five layers in metadata so they surface no matter which namespace the advisor selects.

The retrieval flow follows the same shape as the tree, but it is driven by conversation state rather than raw query text. Diagnose and critique sessions usually begin by updating the `BusinessSnapshot` and asking for missing metrics. Once enough data exists, the advisor retrieves the relevant metric definitions, runs deterministic calculations, and identifies the binding constraint. That constraint determines the follow-up retrieval, which usually means one more namespace from the stack. Design sessions may need unit economics first to pick up CAC ceilings or payback targets that constrain the design space, then pull from a stack namespace. Teach and compare questions can skip the state-building step and retrieve directly.

Any routing or conversation-mode decision is scored separately from retrieval in the eval framework so a bad state/planning decision does not get blamed on the embedder.

Alternatives I considered:

- **One big index.** A diagnostic question about payback gets back results polluted with offer-design content, and vice versa. State-aware namespace selection can't help because there's nothing to select.
- **One namespace per chapter (32 total).** Most queries span several chapters within a layer, and a classifier with 32 targets is noisy enough to be net-negative.
- **An orthogonal cut by industry, ICP, or business stage.** The book isn't organized that way, so the chunker would have to invent metadata that isn't in the text.

---

## 4. Chunking

The transcripts are conversational. A 512-token sliding window splits a named framework across two chunks often enough that retrieval starts returning half-frameworks, and the generator fills in the missing half from priors.

The adopted local chunker is heading-aware: it respects transcript section headings where they exist and falls back to fixed windows where they do not. I also tested a more aggressive framework-aware candidate that splits on framework-like transition phrases. It slightly improved MRR, but the gain was below the adoption threshold, so it is tracked as a candidate rather than adopted as the default.

Measured result:

| Strategy | Hit@1 | Hit@5 | MRR |
|---|---:|---:|---:|
| `heading-aware` | 81.25% | 100.00% | 0.8917 |
| `framework-aware` | 81.25% | 100.00% | 0.8958 |

Report: `evals/reports/chunking_comparison.md`.

The metadata does real work downstream. Hybrid retrieval uses it for filtering. The reranker uses it for context. Citation rendering in the agent's answer pulls chapter and framework name directly from it. A chunk without provenance can't be cited, which means it can't be used.

---

## 5. Hybrid retrieval and rerank

Two properties of the corpus shaped the retrieval design.

The first is that the book uses a lot of named jargon — "rollover upsell," "win-your-money-back," "CAC payback period." Dense embeddings smooth those terms into neighbors, which is what you want for paraphrase robustness and what you don't want when the user types the exact term. Sparse retrieval (BM25) keeps the term as a hard signal. The pipeline runs both and fuses the ranked lists.

I use reciprocal rank fusion rather than weighted score-sum to combine them. Dense cosine scores and BM25 scores live on different scales, so score-sum needs calibration per index and breaks when you swap embedders. RRF works on ranks, so it doesn't care about scale.

The second property is that the downstream token budget is small. The generator gets 3–5 chunks in context, so the top-k from hybrid retrieval has to be sharpened before generation. A cross-encoder reranker (Cohere rerank-3 by default, with a local BGE reranker swappable for cost comparison) reads the query and each candidate together and produces a tighter ordering than either retrieval stage alone.

The first API-backed ablation found that hybrid RRF improved chapter-level Hit@1 and MRR over the BM25 control. I treat that as a pilot result, not selection evidence: it says the retriever finds the expected source chapter high in the list, not that a human judged the exact returned chunks as the best evidence.

The replacement label unit is a required supported claim paired with one or more supporting chunk IDs. A required supported claim is a claim a good answer should be able to make for an eval query; the chunk ID is the human-audited support for that claim. The reviewed labels live in `evals/obligations.jsonl`. The deterministic metric is required-claim support coverage: the fraction of accepted required claims whose supporting chunks appear in retrieved top-k. This is now the primary evidence-support guardrail for retrieval.

Running the retrieval variants against those accepted labels exposed the same limitation from another angle. Dense-only had the best required-claim support coverage, while hybrid RRF improved both chapter-level rank and support coverage versus BM25, but the support labels are not exhaustive. A different unlabeled chunk may support the same claim and still be counted as a miss. Current interpretation: the pilot established that the harness works and that the candidate retrievers return plausible source material, but it did not provide a strong enough evaluation foundation to select a final retrieval approach.

---

## 6. The stateful advisor and its tools

The user-facing entry point is a stateful advisor, first exposed as a CLI. The CLI accepts a business-context directory, maintains a local session snapshot, and calls tools when the state is ready. The point is not to have a clever one-shot prompt; the point is to make the model operate over explicit state and auditable tools.

- `load_business_context(path)` — reads a local directory of business notes, metrics, offer docs, funnel docs, transcripts, and prior session files.
- `update_business_snapshot(message, current_snapshot)` — extracts business facts, metrics, current stack elements, uncertainty, and user goals.
- `plan_next_turn(snapshot, user_goal)` — decides whether to ask a clarifying question, calculate, diagnose, retrieve, critique, draft, compare, or teach.
- `calculate(metric, inputs)` — deterministic Python for the formulas in the book: payback period, CAC ratios, gross profit, LTV.
- `diagnose_constraint(business_snapshot)` — deterministic economics plus source-backed interpretation to identify the binding constraint.
- `retrieve_framework(query, layer?)` — dense/hybrid/rewrite/rerank retrieval once the advisor has a clear target.
- `critique_offer(offer_description, snapshot?)` — retrieves comparable patterns and counter-patterns, returns structured pushback with citations.
- `compare_frameworks(a, b, context?)` — side-by-side retrieval from both relevant namespaces and a structured tradeoff table.
- `draft_offer_stack(snapshot)` — full attraction → upsell → downsell → continuity design with citations.

The reason for splitting it this way:

The arithmetic needs to be deterministic. The model should decide which framework applies and how to phrase the pushback. The payback months should come from Python. `calculate` makes that boundary explicit, and the model can't accidentally produce a hallucinated number for a metric.

The use cases have different shapes. Diagnose and critique need intake plus multi-step reasoning. Calculate is deterministic. Draft and compare are structured generation with their own schemas. A single endpoint can serve all of them, but the prompt has to be a kitchen sink, and the eval criteria collapse into one number that hides regressions.

Each tool has its own success criteria. `load_business_context` is context ingestion coverage. `update_business_snapshot` is field extraction accuracy. `plan_next_turn` is next-action appropriateness. `calculate` is exact-match against expected values. `compare_frameworks` is structured-output validity plus citation coverage. `diagnose_constraint` is constraint-identification accuracy against worked examples and realistic sessions. The eval framework scores each separately.

The orchestration target is a local CLI state graph calling Python services for retrieval and calculation, bounded to 8 tool calls per turn with structured failure on exceed. During development, this can run inside Codex or through Codex CLI. For a deployed product, the same provider boundary can switch to an API key or hosted runtime.

---

## 7. Model routing

A classifier model and a synthesis model differ by roughly two orders of magnitude in cost per token. Routing tiers are the single biggest cost lever in the system.

Three tiers:

- **Cheap** (`gpt-4o-mini` or Haiku) — namespace classification, query rewriting, judge pre-screening.
- **Default** (Sonnet) — synthesis, drafting offer stacks, the tool-use loop driver.
- **Escalation** (Opus) — when a cheap-tier judge's confidence on the default-tier answer falls below threshold, or on an explicit `--quality` flag.

Escalation is triggered by the judge rather than by query-complexity heuristics. Heuristics like "long query goes to the big model" are wrong often enough to be net-negative. A cheap judge reading the cheap-tier answer catches the cases where escalation actually pays off, and the judge runs on the cheap tier so the overhead stays small.

There's a script that reads the eval store and prints lines like "for namespace-classification queries, `gpt-4o-mini` matches Sonnet at 97% accuracy and 1/30th cost — switch." That's the artifact for "model-switching decisions based on data" in the JD.

Cost control also starts before generation. Embeddings are deterministic for the same text and model, so the local OpenAI embedding client writes them to `.cache/embeddings.sqlite3` using a model + text hash key. The first uncached retrieval ablation spent API tokens to embed the corpus and queries; subsequent runs hit the cache and made no duplicate embedding calls. That gives the project a concrete cost-saving artifact now, not just a planned optimization.

---

## 8. Pilot Results So Far

The local proof harness establishes a BM25 control group before adding dense embeddings, Pinecone, hybrid retrieval, or reranking. These results are included as pilot evidence: they validate the mechanics of the evaluation harness and reveal where the evaluation design is too weak. They are not presented as final model-selection evidence.

| Report | Question | Result | Decision |
|---|---|---|---|
| `evals/reports/local_retrieval_baseline.md` | What can the simplest local retriever do? | Hit@1 81.25%, Hit@5 100.00%, MRR 0.8917 | Use as the control group |
| `evals/reports/chunking_comparison.md` | Do structured chunks beat fixed windows? | `heading-aware` beats fixed windows on Hit@1 and MRR; `framework-aware` has tiny MRR gain | Keep `heading-aware` unless another guardrail justifies switching |
| `evals/reports/retrieval_ablation.md` | Can the harness compare BM25, dense, and hybrid repeatably? | `hybrid-rrf` and `hybrid-rrf-lexical-anchor` Hit@1 87.50%, MRR 0.9375 vs BM25 Hit@1 81.25%, MRR 0.8917 | Useful pilot signal, but chapter-level labels are too coarse for final selection |
| `evals/reports/required_claim_review_status.md` | Can required-claim labels be reviewed consistently? | 65 labels accepted, none needing attention | Useful answer-readiness labels, not exhaustive chunk-relevance judgments |
| `evals/reports/obligation_support_coverage.md` | Do retrieved chunks hit known support chunks? | BM25 heading-aware covers 87.69% of 65 accepted labels; 8 unsupported claims remain | Useful support sanity check, but incomplete because alternative good chunks may be unlabeled |
| `evals/reports/retrieval_required_claim_ablation.md` | What happens when variants are scored against known support chunks? | `dense-openai` covers 90.77%, `hybrid-rrf` 89.23%, BM25 87.69%, lexical-anchor 87.69% | Shows candidates are close and the label design is insufficient for final selection |
| `.cache/embeddings.sqlite3` + `src/money_model_architect/embeddings.py` | Can API embedding experiments be rerun without repeated embedding spend? | Warm reruns report 0 API tokens and cache hits for embedded corpus/query texts | Keep SQLite embedding cache locally; make it Redis or persistent-vector-store backed in production |

This matters because it shows the system did not start by assuming a technique would win. The pilot made the comparison harness concrete, but it also showed that the first label design was not robust enough to choose between close retrieval approaches.

Reliability note:

- The chapter-level retrieval metrics are valid screening metrics, not final human relevance judgments. They measure whether the expected chapter appears high in the retrieved list.
- The current pilot queries are not realistic enough for final retrieval selection. Many use exact framework vocabulary from the corpus, which can artificially favor lexical retrieval. A robust query set needs exact-name queries, paraphrases, messy business-situation questions, diagnostic numeric scenarios, and confusable near-neighbor questions.
- Required-claim support coverage is a stronger evidence-readiness metric, but it only checks against labeled support chunks. It can miss alternative chunks that are equally good but unlabeled.
- Because the current variants are close and the labels are incomplete, the next methodology must judge retrieved chunks directly rather than infer quality from chapter IDs or a non-exhaustive support list.

## 9. Chunk-level relevance results

The realistic-query evaluation now has a chunk-level relevance pool: 312 query/chunk pairs across 36 realistic queries. Four `gpt-5.5` subagents labeled the blind pool, then I adjudicated the 119 rows where `gpt-4o-mini` and `gpt-5.5` disagreed. The adjudicated label set is `evals/chunk_relevance_pool.adjudicated_v1.jsonl`; the score report is `evals/reports/pooled_relevance_adjudicated_v1.md`.

Overall result:

| Retriever | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.6701 | 0.7667 | 0.5660 |
| `dense-openai` | 0.7647 | 0.8611 | 0.6561 |
| `hybrid-rrf` | 0.7357 | 0.8667 | 0.6482 |

At the aggregate level, dense retrieval is the best default: it has the strongest rank quality and recall. Hybrid RRF has a small precision edge, but not enough to win overall.

The more important result is by query type:

| Query type | Queries | BM25 nDCG@5 | Dense nDCG@5 | Hybrid nDCG@5 | Dense - Hybrid |
|---|---:|---:|---:|---:|---:|
| `business_situation` | 8 | 0.728 | 0.797 | 0.768 | +0.028 |
| `confusable` | 6 | 0.548 | 0.767 | 0.718 | +0.049 |
| `diagnostic_numeric` | 6 | 0.822 | 0.591 | 0.742 | -0.151 |
| `exact_framework` | 6 | 0.595 | 0.788 | 0.632 | +0.156 |
| `noisy_vague` | 4 | 0.729 | 0.848 | 0.767 | +0.080 |
| `paraphrase` | 6 | 0.598 | 0.815 | 0.786 | +0.029 |

Interpretation: dense retrieval wins most semantic query categories, but diagnostic numeric prompts are a real exception when treated as standalone retrieval questions. In those cases, the query contains several concrete metrics (`CAC`, gross profit, margin, LTV, payback), and dense retrieval over-associates the question with CAC because CAC is explicitly mentioned. Hybrid and BM25 preserve the lexical metric mix and more reliably pull the gross-profit, CFA, context, and money-model diagnosis chunks that explain the bottleneck.

Examples:

- `diagnostic_low_first_month_gp`: dense ranks `cac` chunks above `gross-profit` and `cfa`; hybrid puts `gross-profit:0`, `cfa:1`, and `context:1` in the top 5.
- `diagnostic_ltv_good_payback_bad`: dense finds general CAC/gross-profit chunks; hybrid and BM25 surface the money-model/payback context needed to distinguish high LTV from slow payback.
- `situation_paid_ads_breakeven_slow`: dense focuses on CAC mechanics; hybrid moves `gross-profit:0` and `context:1` into the top 3.

I then tested whether the diagnostic weakness was caused by the smaller embedding model. For the six `diagnostic_numeric` queries, I reran dense and hybrid retrieval using `text-embedding-3-large`. That introduced seven new top-5 query/chunk pairs, which were adjudicated and added to `evals/chunk_relevance_pool.diagnostic_embedding_expansion.jsonl`. The report is `evals/reports/diagnostic_embedding_comparison.md`.

Diagnostic-only result after adding the `text-embedding-3-large` rows:

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.7703 | 0.9333 | 0.5734 |
| `dense-openai-3-small` | 0.5391 | 0.8000 | 0.4773 |
| `hybrid-rrf-3-small` | 0.6886 | 0.9000 | 0.5318 |
| `dense-openai-3-large` | 0.7193 | 0.9000 | 0.5318 |
| `hybrid-rrf-3-large` | 0.7145 | 0.9000 | 0.5318 |

This result narrows the root cause. `text-embedding-3-large` substantially improves dense diagnostic retrieval, so the issue is partly embedding quality. But BM25 is still strongest on the diagnostic slice, which means lexical preservation of metric terms still matters. The product implication is not "use larger dense embeddings everywhere." It is that raw diagnostic prompts should not be the primary retrieval unit.

- In a real session, first build the `BusinessSnapshot` from the user's messages and local business-context directory.
- Then calculate the economic state where possible.
- Then retrieve using the diagnosed constraint, not the messy user wording.
- Keep lexical-preserving retrieval as a fallback because metric names and numbers matter.

I then tested the third option: diagnose first, rewrite the query, and retrieve from the rewritten diagnostic intent. The script is `scripts/diagnostic_rewrite_experiment.py`; the report is `evals/reports/diagnostic_rewrite_experiment.md`. The rewrite uses deterministic unit-economics logic where possible:

- low first-month GP -> `monetization`
- high revenue / low margin -> `gross-margin`
- good LTGP but slow payback -> `cash-constraint`
- free offer overload -> `free-offer-quality`
- month-three churn discount -> `continuity-retention`
- 2x CAC in first 30 days -> `scale-ready`

Diagnostic rewrite result:

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.7017 | 0.9333 | 0.4269 |
| `dense-openai-3-small` | 0.4890 | 0.8000 | 0.3636 |
| `hybrid-rrf-3-small` | 0.6238 | 0.9000 | 0.4084 |
| `dense-openai-3-large` | 0.6548 | 0.9000 | 0.4084 |
| `hybrid-rrf-3-large` | 0.6536 | 0.9000 | 0.4084 |
| `diagnose-rewrite-bm25` | 0.9142 | 0.9667 | 0.4454 |

The result supports a task-specific retrieval policy for benchmarked diagnostic prompts: do not send the raw user query directly to dense retrieval. First identify the economic constraint, rewrite the retrieval target around the relevant metric/framework terms, then retrieve. In the product architecture, that "rewrite" is better understood as retrieving from the structured `BusinessSnapshot` and diagnosed constraint.

I also tested whether this path can be selected on the benchmark without cheating by reading the eval label. The report is `evals/reports/routed_retrieval_policy.md`. The router uses only query text and sends a query to diagnose-first retrieval when it contains all three signals:

- a number;
- a business metric term such as CAC, gross profit, payback, churn, cancellation, discount, retention, or margin;
- diagnostic intent language such as "what is the bottleneck," "what metric," "what part of the money model," "is this working," "what are we trying to improve," or "what does that imply."

On the current 36-query realistic set, that router selected all six `diagnostic_numeric` queries and no non-diagnostic queries. The full-set routed policy then scored as follows:

| Variant | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| `bm25` | 0.6500 | 0.7667 | 0.5280 |
| `dense-default` | 0.7478 | 0.8611 | 0.6247 |
| `hybrid-default` | 0.7161 | 0.8667 | 0.6141 |
| `routed-dense-or-diagnose-rewrite` | 0.8187 | 0.8889 | 0.6383 |

By query type, the routed policy keeps dense's wins on semantic query categories and replaces dense only where it fails:

| Query type | BM25 | Dense | Hybrid | Routed policy |
|---|---:|---:|---:|---:|
| `business_situation` | 0.728 | 0.797 | 0.768 | 0.797 |
| `confusable` | 0.548 | 0.767 | 0.718 | 0.767 |
| `diagnostic_numeric` | 0.702 | 0.489 | 0.624 | 0.914 |
| `exact_framework` | 0.595 | 0.788 | 0.632 | 0.788 |
| `noisy_vague` | 0.729 | 0.848 | 0.767 | 0.848 |
| `paraphrase` | 0.598 | 0.815 | 0.786 | 0.815 |

This answers a narrow benchmark question: the current diagnostic prompt set is separable from the rest of the query set, and replacing raw dense retrieval with diagnose-first retrieval improves the measured result. It does not establish that a regex-like query router is a production design. For the product, this is evidence for a stateful advisor that gathers facts and diagnoses before retrieval.

Decision implication: do not simply replace dense with hybrid everywhere, and do not build the advisor around a brittle single-turn diagnostic router. Use dense as the default retriever for teach/compare/semantic questions. For diagnose/design/critique sessions, build conversation state first, calculate where possible, then retrieve source material for the diagnosed or designed constraint. The next implementation work should compare:

| Diagnostic strategy | Hypothesis |
|---|---|
| Dense default | Strong semantic retrieval, but may overweight the first named metric in numeric prompts |
| Hybrid for diagnostic queries | BM25 term preservation should recover gross-profit/CFA/payback chunks |
| Snapshot-driven retrieval | Extract and maintain the business facts first, then retrieve for the diagnosed constraint |
| Two-stage diagnostic retrieval | Calculate the bottleneck, then retrieve framework fixes from the identified constraint |

---

## 10. Experiment-driven architecture

The design should not depend on a priori confidence in any one RAG technique. It should treat chunking, retrieval, reranking, model routing, and tool boundaries the way an ML project treats model families and hyperparameters: define the search space, run controlled comparisons, keep the winner only if it improves the metrics that matter.

The first implementation has a 32-query pilot set (`evals/golden.jsonl`), a local retrieval baseline, a chunking comparison, and accepted required-claim support labels. The next evaluation iteration uses `evals/realistic_queries.jsonl` and the methodology in `evals/reports/query_realism.md` before selecting a retriever. The full system expands that into the following experiment matrix.

| Decision | Baseline | Variants | Primary metric | Guardrail | Decision rule |
|---|---|---|---|---|---|
| Namespace design | One corpus-wide index | Five layer namespaces; per-chapter namespaces; layer + secondary-role metadata | Router accuracy, retrieval hit@5 | Empty-retrieval rate | Keep namespaces only if hit@5 improves without routing failures exceeding threshold |
| Query set design | Framework-name pilot queries | Exact-name, paraphrase, business-situation, diagnostic numeric, confusable, and noisy queries | Query realism coverage | Lexical-overlap audit | Do not choose a retriever until the eval set includes realistic user-intent queries |
| Chunking | Fixed 512-token windows | Framework-aware chunks; heading-aware chunks; 400/700/1000-token targets; overlap on/off | Chapter-level MRR | Context token count, support coverage when revisited | Pick the simplest chunks that preserve retrieval quality; revisit only if pooled relevance labels show better support |
| Embeddings | `text-embedding-3-large` | `text-embedding-3-small`; Cohere embed; local BGE | Hit@5, MRR | Cost/query, latency | Use the cheapest model whose retrieval score is within an acceptable delta of the best model |
| Retrieval | BM25-only | OpenAI dense; dense + BM25 RRF; snapshot-driven retrieval; query rewrite on/off | Hit@1, MRR, nDCG@5 | Required-claim support coverage, p95 latency | Use hybrid or rewrite only where chunk relevance improves enough to justify complexity |
| Chunk relevance evaluation | Chapter labels only | Human judgments over retrieved chunks from BM25, dense, and hybrid | nDCG@5, precision@5, recall@5 | Labeling time | Add only enough labels to decide close retrieval/rerank choices |
| Fusion | Dense rank only | Weighted score sum; reciprocal rank fusion | nDCG@10 on pooled judgments | Tuning complexity | Prefer RRF unless score-sum beats it after calibration on held-out queries |
| Reranking | No reranker | Cohere rerank; local BGE reranker; top-20 vs top-50 candidates | nDCG@5, precision@5 | p95 latency, cost/query | Keep rerank only if precision gain survives cost and latency guardrails |
| Context size | Top 5 chunks | Top 3, 8, 10; summarization fallback | Faithfulness, answer completeness | Token budget | Use the smallest context that preserves answer quality and required citations |
| Conversation state | Stateless single-turn query | `BusinessSnapshot`; session memory; local business-context directory; clarify-before-retrieve planner | next-action accuracy, field extraction accuracy | user turns to resolution | Keep state explicit if it improves diagnosis/design correctness and reduces premature retrieval |
| Tool surface | Single `/query` endpoint | Stateful advisor tools; fewer merged tools; explicit calculate-only path | Task success by use case | Tool-loop failures | Keep separate tools when they make eval criteria cleaner or reduce hallucinated arithmetic |
| Model routing | One default synthesis model | Cheap router; cheap judge; escalation threshold sweep | Quality/cost frontier | Refusal and structured-output failures | Route down when cheap models match quality; escalate only where judge confidence predicts improvement |
| Prompt strategy | One general system prompt | Use-case prompts; schema-first outputs; critique-specific rubric | Faithfulness, structured validity | Token count | Split prompts when per-use-case quality improves without making maintenance noisy |

Each report should have the same shape:

```text
Hypothesis
Variants tested
Dataset slice
Metrics
Results table
Decision
Failure analysis
Next experiment
```

This is the ML-style discipline I want the project to show: not "hybrid retrieval is good because a coarse metric moved," but "the pilot metrics were useful enough to reveal their own limitations, so the evaluation was redesigned before making a retrieval decision."

---

## 11. Evaluation

The eval framework is what makes everything else changeable. With it in place, swapping an embedder or a chunking strategy or a tier mapping takes minutes to validate. Without it, every change is a guess.

Five components:

**Golden dataset.** The current 32 hand-built records in `evals/golden.jsonl` are a pilot set, not the final retrieval benchmark. They use query, target layer, and expected chapters. These chapter labels are deliberately coarse, so they support fast screening but not final chunk-ranking claims. The stronger retrieval-support label set is `evals/obligations.jsonl`: required supported claims paired with supporting chunk IDs and a review status. The next benchmark should be built around realistic user-intent queries, not mostly framework-name queries.

**Automated quality scoring.** Three signals kept separate: faithfulness (LLM judge with a strict prompt, scored binary per claim, then averaged), citation coverage (fraction of required citations actually used), and answer-ideal cosine similarity as a cheap secondary signal. Keeping them separate matters because the dashboard needs to show which dimension regressed.

**Retrieval metrics.** The current Hit@k and MRR scores are chapter-level screening metrics: they catch whether the expected source chapter is retrieved high enough to be useful. For final chunk-ranking decisions, pooled human relevance labels are required. Once those labels exist, the primary metrics become nDCG@5/nDCG@10, precision@5, and recall@5 over chunk-level judgments.

**Latency benchmarks.** Per-stage p50/p95/p99 for embedding, vector search, BM25, fusion, rerank, and generation. End-to-end latency without breakdown isn't actionable — a regression that doubles rerank latency looks the same as one that doubles generation latency.

**Regression detection.** The eval suite runs on every PR via GitHub Actions. `baseline.json` in the repo holds last-known-good scores. The CI gate fails if any metric drops past its configured threshold. Thresholds rather than strict equality because LLM-judge non-determinism has a noise floor.

---

## 12. Observability and failure modes

Every request emits one row to an event store: request ID, tier, model, namespaces hit, tokens in / cached / out, cost, per-stage latency, tool calls, judge score, and failure mode if any. SQLite locally, Postgres for production. A Next.js dashboard reads the store and renders cost, tokens, quality, latency, and anomalies.

Anomalies are detected against a rolling 24h baseline with σ thresholds, with flat thresholds layered on top for absolute floors (cost-per-request above some dollar value, refusal rate above some percentage). The σ part catches regressions that look normal in absolute terms but are several times yesterday's variance.

Failures get a taxonomy: `provider_error`, `structured_output_invalid`, `tool_loop_exceeded`, `refusal`, `hallucination_suspected`, `empty_retrieval`. Each has a handler. The rates by category are what's actionable — a spike in `structured_output_invalid` after a model swap is a specific, debuggable signal in a way that an overall error rate isn't.

---

## 13. Mapping to the JD

The pieces the JD calls out (multiple Pinecone namespaces, chunking strategy, embedding model selection, hybrid retrieval, reranking, golden datasets, automated quality scoring, retrieval metrics, latency benchmarks, regression detection, model routing, observability, anomaly detection) are all in here. Section 20 of [ARCHITECTURE.md](ARCHITECTURE.md) maps each one to the file it lives in.
