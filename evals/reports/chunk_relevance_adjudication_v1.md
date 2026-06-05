# Chunk Relevance Adjudication v1

## Scope

- Total rows: 312
- Rows where models agreed and were accepted: 193
- Rows personally adjudicated by Codex because labels disagreed: 119

## Final Label Counts

| Label | Rows |
|---:|---:|
| 2 | 152 |
| 1 | 95 |
| 0 | 65 |

## Disagreement Votes

| Selected perspective | Rows |
|---|---:|
| `gpt-4o-mini` | 27 |
| `gpt-5.5` | 91 |
| `neither` | 1 |

## Notes

- Agreement rows were not rereviewed; the shared model label was accepted.
- Disagreement rows include `gpt_4o_mini_relevance`, `gpt_5_5_relevance`, and `adjudication_note` fields in the JSONL.
- This is still an internal adjudication pass, not an independent external human benchmark.
