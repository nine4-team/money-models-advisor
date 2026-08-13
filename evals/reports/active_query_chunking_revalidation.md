# Active-Query Chunking Revalidation

## Method

All five chunking strategies used the same 46 cases, frozen `gpt-5.5` corpus-guided queries, `text-embedding-3-small`, unfiltered local hybrid retrieval, and top-five cutoff. The answer key is anchored to audited heading passages; alternative boundaries inherit labels by source-span overlap. The later framework-boundary audit reviewed 115 pairs with no previously returned heading counterpart and every weak-overlap positive. Across the current framework results, 12 missed useful labels were added and one overly broad label was removed.

“Mean top-five words” is the total text returned across five chunks.

## Results

| Strategy | Hit@1 | Hit@3 | Hit@5 | Mean rank | Useful@5 | Noise@5 | Max chunk words | Mean top-five words |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed-300 | 91.3% | 97.8% | 97.8% | 1.089 | 79.1% | 20.9% | 436 | 1,490 |
| fixed-512 | 87.0% | 97.8% | 97.8% | 1.156 | 79.6% | 20.4% | 729 | 2,495 |
| fixed-800 | 95.7% | 100.0% | 100.0% | 1.065 | 75.2% | 24.8% | 1,139 | 3,762 |
| heading-aware | 93.5% | 97.8% | 100.0% | 1.130 | 73.0% | 27.0% | 2,471 | 2,493 |
| framework-aware | 93.5% | 97.8% | 100.0% | 1.152 | 78.7% | 21.3% | 922 | 2,476 |

## Decision

Use framework-aware chunking. It ties heading-aware on Hit@1 and Hit@5, improves useful-result density, and eliminates the long-section outliers. Fixed-800 ranks a useful result first in one additional case, but its top-five context is 51% larger.

Machine-readable outputs:

- `evals/reports/active_query_chunking_revalidation_summary.json`
- `evals/reports/active_query_chunking_revalidation_cases.jsonl`
- `evals/active_query_chunking_adjudications.jsonl`
