# Eval Fixtures

Fixtures are test-only inputs for repeatable eval cases.

They are not production business state.

## Snapshots

`snapshots/` contains starting `BusinessSnapshot` states copied into isolated eval business directories before each case runs.

## Sessions

`sessions/` contains small prior-turn fixtures for cases that should inspect saved conversation history.

## Local Docs

`local_docs/` contains small local business-doc fixtures for cases that should inspect business files before updating the snapshot.

Eval runs must copy these fixtures into generated run directories and must not mutate the real `/Users/benjaminmackenzie/1584_design` advisor state.
