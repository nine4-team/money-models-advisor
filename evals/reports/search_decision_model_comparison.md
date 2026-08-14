# Search-Decision Model Comparison

## Method

One blind pass over 48 frozen cases per model. For each trial, the deterministic harness loaded current advisor state, recent turns, and local business documents, then the model made only the semantic search/no-search decision. Retrieval, answer generation, shell use, labels, evaluator rationales, prior trials, and evaluation documents were excluded.

Dataset SHA-256: `dbeed4ec8fb20571ffab236239dd7cef7b234ecd8f13c0f0b1c6c686fa8ea765`.

## Results

| Model | Decision accuracy | Required-search recall | No-search accuracy | Valid trials | p50 latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|
| `gpt-5.5` | 100.0% (48/48) | 100.0% (24/24) | 100.0% (24/24) | 48/48 | 11.4 s | 14.6 s |
| `gpt-5.4-mini` | 97.9% (47/48) | 95.8% (23/24) | 100.0% (24/24) | 48/48 | 10.4 s | 13.1 s |

## Error and label audit

The single apparent error was reviewed against the current search rule and the
loaded business context. The label stands. The user asked how to change payment
timing without reducing the offer; the saved offer context was sufficient to
search for source-grounded payment-plan guidance. Mini instead required unrelated
acquisition economics and chose no search.

No false positive was found. GPT-5.5 had no false negatives; Mini had one.

## Decision

Keep `gpt-5.5` as the operating agent. Mini is viable for this gate but did not
match GPT-5.5's perfect single-pass result. Mini remains the validated bounded
query-writer option established by the separate retrieval experiment.

## Cases Requiring Audit

| Model | Case | Expected | Actual | Valid | Issue |
|---|---|---|---|---:|---|
| `gpt-5.4-mini` | `searchdecision_v1_007` | `search_source_material` | `no_search` | yes | decision error |

Raw artifacts: `evals/runs/search_decisions/balanced_v1/`
