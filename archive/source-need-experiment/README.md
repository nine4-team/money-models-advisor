# Retired Source-Need Experiment

This directory preserves the earlier filtered, multi-query retrieval experiment and
the model-routing harnesses that depended on it. The active product no longer exposes
that contract.

The current runtime accepts one agent-authored `SearchRequest` containing `intent`,
`user_turn`, and a single corpus-guided `query`. Current retrieval evidence is in
`../../evals/reports/active_framework_retrieval_matrix.md`.

Files here are frozen historical artifacts. Scripts retain their original imports
and paths for inspection and are not part of the supported command surface or stable
regression gate.
