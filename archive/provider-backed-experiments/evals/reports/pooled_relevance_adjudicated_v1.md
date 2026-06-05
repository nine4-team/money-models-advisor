# Pooled Chunk Relevance

## Purpose

Score retrievers using blind query/chunk relevance judgments over the realistic query set.

Current labels are internal evaluation labels from Codex GPT-5 Codex (119 rows), OpenAI gpt-5.5 (193 rows), not an external human benchmark. They are useful for comparing retrieval choices and identifying rows that deserve further audit.

## Review Status

- Pool rows: 312
- Reviewed rows: 312
- Unreviewed rows: 0

## Label Provenance

| Source | Provider | Model | Reviewer | Rows |
|---|---|---|---|---:|
| `codex_adjudicated_v1` | `Codex` | `GPT-5 Codex` | `codex_adjudicator_v1` | 119 |
| `subagent_first_pass` | `OpenAI` | `gpt-5.5` | `subagent-01-gpt-5.5` | 55 |
| `subagent_first_pass` | `OpenAI` | `gpt-5.5` | `subagent-02-gpt-5.5` | 37 |
| `subagent_first_pass` | `OpenAI` | `gpt-5.5` | `subagent-03-gpt-5.5` | 52 |
| `subagent_first_pass` | `OpenAI` | `gpt-5.5` | `subagent-04-gpt-5.5` | 49 |

## Label Distribution

| Label | Meaning | Rows |
|---:|---|---:|
| 2 | Directly useful / cite-worthy | 152 |
| 1 | Partially useful / background | 95 |
| 0 | Not useful | 65 |

## Metrics

| Variant | Queries Scored | nDCG@5 | Precision@5 | Recall@5 |
|---|---:|---:|---:|---:|
| `bm25` | 36 | 0.6701 | 0.7667 | 0.5660 |
| `dense-openai` | 36 | 0.7647 | 0.8611 | 0.6561 |
| `hybrid-rrf` | 36 | 0.7357 | 0.8667 | 0.6482 |

## Decision

The chunk-level labels separate the candidates more clearly than the pilot chapter-level metrics: dense retrieval currently leads on nDCG@5 and recall@5, hybrid RRF is close, and BM25 trails both. Before treating this as the final retrieval decision, audit the remaining low-confidence labels and the queries where dense and hybrid disagree.
