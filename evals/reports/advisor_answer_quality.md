# Advisor Answer-Quality Audit

## Method

Codex reviewed the six frozen current-path answers against the saved snapshot, user turn, and exact cited passages. The audit checks whether the recommendation is reasonable and useful and whether each material source-backed claim is supported by its cited text. Answer hashes prevent a changed answer from inheriting an old judgment.

## Results

- Current audited answers: 6 / 6
- Correct recommendations: 6 / 6
- Useful recommendations: 6 / 6
- Supported source-backed claims: 14 / 14

| Case | Current audit | Correct | Useful | Supported claims |
|---|---:|---:|---:|---:|
| `sourceevents_v1_001` | yes | yes | yes | 4 / 4 |
| `sourceevents_v1_002` | yes | yes | yes | 3 / 3 |
| `sourceevents_v1_003` | yes | yes | yes | 2 / 2 |
| `sourceevents_v1_004` | yes | yes | yes | 0 / 0 |
| `sourceevents_v1_005` | yes | yes | yes | 2 / 2 |
| `sourceevents_v1_006` | yes | yes | yes | 3 / 3 |

## Corrections Found

The first audit found two unsupported or overstated formulations: a front-end offer was described as necessarily paid, and a continuity answer attached citations to wording stronger than the passages supported. The operating skill now requires a claim-by-claim support check before `session finish`. Those two cases and one additional citation-specific case were rerun blind; the current answers pass both the source-event scorer and this semantic audit.

## Scope

This is a six-case, single-reviewer regression, not a population estimate. Codex performed the semantic review; the deterministic runtime still enforces citation provenance and calculation correctness, while this eval measures semantic support and recommendation quality.
