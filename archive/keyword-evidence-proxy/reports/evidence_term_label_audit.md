# Evidence Term Label Audit

## Purpose

Evidence-term coverage is a cheap proxy for whether retrieved chunks contain answer-supporting details. It is not a final faithfulness score. This audit checks whether labels are source-present and flags labels that may be too generic to support decision-grade conclusions.

## Summary

- Labeled records: 16
- Terms absent from expected chapters: 3
- Possibly generic terms: 34

## Findings

| Record | Absent Terms | Possibly Generic Terms |
|---|---|---|
| `payback_definition` | - | `first 30 days` (18 chapters), `upsell` (19 chapters), `gross profit` (10 chapters) |
| `rollover_upsell` | - | `credit` (14 chapters) |
| `continuity_churn` | - | `month` (26 chapters), `cancel` (7 chapters) |
| `feature_downsell` | - | `feature` (7 chapters), `lower price` (11 chapters), `guarantee` (8 chapters) |
| `free_offer_cac` | - | `free` (26 chapters), `leads` (17 chapters), `CAC` (8 chapters) |
| `cac_fully_loaded` | - | `advertising` (14 chapters) |
| `gross_profit_service_margin` | - | `gross profit` (10 chapters), `80` (13 chapters), `service` (20 chapters) |
| `ltgp_cac_viability` | - | `CAC` (8 chapters), `3` (13 chapters), `revenue` (11 chapters) |
| `cfa_levels` | `level 1`, `level 2`, `level 3` | `level 3` (8 chapters) |
| `payback_gross_profit_not_revenue` | - | `gross profit` (10 chapters), `revenue` (11 chapters), `break even` (16 chapters) |
| `anchor_upsell` | - | - |
| `payment_plans` | - | `today` (14 chapters), `payment plan` (10 chapters) |
| `continuity_bonus` | - | `bonus` (9 chapters), `first month` (26 chapters), `continuity` (12 chapters) |
| `continuity_discount` | - | `cancel` (7 chapters) |
| `waived_fee` | - | `cancel` (7 chapters) |
| `money_model_stack` | - | `attraction` (14 chapters), `upsell` (19 chapters), `downsell` (9 chapters), `continuity` (12 chapters) |

## Decision

Treat citation-completeness results as provisional until the evidence terms are manually reviewed against the transcript spans they are meant to support. Retrieval rank metrics remain valid because they are based on expected chapters, not these proxy labels.

## Next Labeling Pass

- Replace generic single-word labels with source-grounded answer facts or short phrases.
- For each labeled query, record why each term is answer-critical.
- Add `required_evidence_spans` or `must_cite_chunks` for the highest-value eval records so citation scoring is not only keyword based.
