# Chunking Comparison

## Hypothesis

Framework or heading-aware chunks should retrieve named Money Models concepts more precisely than naive fixed windows, because the transcripts are organized around concepts, examples, and numbered frameworks.

## Variants

| Strategy | Chunks | Avg Words | Hit@1 | Hit@5 | MRR | p95 Latency |
|---|---:|---:|---:|---:|---:|---:|
| `fixed-300` | 360 | 308.1 | 65.62% | 100.00% | 0.8099 | 0.661 ms |
| `fixed-512` | 215 | 507.1 | 71.88% | 100.00% | 0.8448 | 1.042 ms |
| `fixed-800` | 141 | 761.4 | 75.00% | 100.00% | 0.8552 | 0.27 ms |
| `heading-aware` | 202 | 513.5 | 81.25% | 100.00% | 0.8917 | 0.44 ms |
| `framework-aware` | 204 | 496.9 | 81.25% | 100.00% | 0.8958 | 0.408 ms |

## Decision

`framework-aware` is the metric winner on MRR in this local BM25 comparison. The adopted default remains `heading-aware` because adoption requires either a Hit@1 improvement or an MRR gain of at least 0.01 over the simpler heading-aware baseline.

Measured delta vs `heading-aware`: Hit@1 +0.00%, MRR +0.0041.

## Failure Analysis

- `fixed-300` had no hit@5 misses.
- `fixed-512` had no hit@5 misses.
- `fixed-800` had no hit@5 misses.
- `heading-aware` had no hit@5 misses.
- `framework-aware` had no hit@5 misses.

## Next Experiment

Score the retrieval variants against accepted required-claim labels. The framework-aware candidate can be revisited if a future support-coverage run shows that it retrieves better supporting chunks, but the current retrieval-quality gain is below the adoption threshold.
