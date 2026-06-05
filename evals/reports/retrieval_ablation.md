# Retrieval Ablation

## Hypothesis

Dense embeddings and hybrid retrieval should improve semantic or paraphrased query retrieval over the BM25 control, but they must earn their additional API cost and implementation complexity.

## Variants

| Variant | Status | Hit@1 | Hit@5 | MRR | p95 Latency | Notes |
|---|---|---:|---:|---:|---:|---|
| `bm25` | ok | 81.25% | 100.00% | 0.8917 | 0.386 ms |  |
| `dense-openai` | ok | 81.25% | 100.00% | 0.8958 | 12.328 ms | 0 API tokens, 234 cache hits |
| `hybrid-rrf` | ok | 87.50% | 100.00% | 0.9375 | 11.875 ms | RRF over top 20 |
| `hybrid-rrf-lexical-anchor` | ok | 87.50% | 100.00% | 0.9375 | 11.875 ms | RRF top 4 + BM25 anchor |

Cost note: embedding experiments use deterministic vectors cached in `.cache/embeddings.sqlite3`, keyed by model and text hash. This run reported 0 API tokens and 234 cache hits for `dense-openai`; the first uncached run pays to embed corpus/query texts, while warm reruns avoid duplicate embedding calls.

## Decision

`hybrid-rrf`, `hybrid-rrf-lexical-anchor` are tied metric winners in this run. Adopt a non-BM25 default only if it improves Hit@1 or increases MRR by at least 0.01 without regressing accepted required-claim support coverage.

Measured delta vs `bm25`: Hit@1 +6.25%, MRR +0.0458.

## Failure Analysis

- `bm25` had no hit@5 misses.
- `dense-openai` had no hit@5 misses.
- `hybrid-rrf` had no hit@5 misses.
- `hybrid-rrf-lexical-anchor` had no hit@5 misses.

## Next Experiment

If dense or hybrid improves retrieval, run required-claim support coverage across the winning retrieval variant. If not, keep BM25 locally and defer dense retrieval until paraphrase-heavy eval records are expanded.
