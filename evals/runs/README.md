# Saved Evaluation Runs

The active directories contain structured artifacts used by the current scorers and
narrative evidence renderer. `archive/` contains superseded runs. Generated
`codex_stdout.txt` and `codex_stderr.txt` transport logs are intentionally excluded;
the repository retains the prompts, structured results, model metadata, and final
outputs needed to inspect the experiments. Developer-specific absolute paths in
current artifacts are normalized to `<repo>` and `<business-context>`.
