# Current Remediation Plan

**Updated:** 2026-08-17

This is the canonical list of known gaps that could make the implementation,
evaluation evidence, and `narrative.html` disagree. Older design and evaluation
plans remain useful history, but open remediation work should be tracked here.

The goal is not to add sophistication. The goal is to make the system internally
consistent, make every important choice traceable to evidence, and state only what
the current implementation and tests prove.

## Recently resolved

- Query generation now compares the raw question, an unguided rewrite, and a
  corpus-guided rewrite across `gpt-5.5` and `gpt-5.4-mini`.
- The saved queries were compared through both BM25 and hybrid retrieval on the
  46-case suite.
- Returned passages were checked for missing useful labels and overly broad labels.
- The search gate was tested once per model on 48 balanced cases across five
  business contexts. The isolated harness supplied current business context and
  excluded retrieval, answer generation, shell use, labels, and prior trials. The
  result and label audit are recorded in
  `evals/reports/search_decision_model_comparison.md`.
- All five chunking strategies were replayed on the active single-query hybrid path;
  framework-aware chunking became the runtime default.
- Framework-aware chunks were indexed in Pinecone and replayed across all 46 cases.
- One namespace was compared with Unit Economics, Offers, Upsells, Downsells, and
  Continuity namespaces. The split did not improve retrieval quality, so one
  namespace remains the active design.

## Priority 1 — Correct claims that are already known to be wrong — Complete

These changes require no new experiment.

**Status:** Completed in `narrative.html` on 2026-08-12. Keep the items below as
the acceptance record for future narrative audits.

### 1. Describe the actual guardrails

**Original problem:** The narrative said the CLI prevented ungrounded citations and
unproven math. Citation validation still proves provenance rather than semantic
support. Calculation validation has since been strengthened: `session finish`
recomputes supported metrics and rejects invalid inputs or mismatched results.

**Remediation:** Rename these as citation-provenance and calculation-trace checks.
State their exact limits.

**Complete when:** The component card, guardrails section, workflow labels, and
appendix make no semantic-grounding or math-correctness claim that the validator does
not enforce.

### 2. Separate reference-label validation from model performance

**Problem:** The narrative says the perfect 24-case reference traces “clear” the
upstream search decision. That verifies the cases and scorer, not the operating
model. The model comparison itself is below 100%.

**Remediation:** Explain that the reference traces validate the scoring setup, then
report model performance separately in the orchestration section.

**Complete when:** No sentence treats answer-key/reference performance as observed
runtime-agent performance.

### 3. Replace the stale latency limitation

**Problem:** The limits section cites the older 1.4s/1.8s multi-query benchmark and
says the active single-query path still needs request-level measurement. The active
path has now been measured at 4.07s p50 and 7.64s p95.

**Remediation:** Use the active-path result and state that hosted latency optimization
remains open.

**Complete when:** The limits section agrees with the current Pinecone results in
Section 3.3 and `evals/reports/active_query_pinecone_revalidation.md`.

### 4. Fix dataset units and reviewer disclosure

**Problem:** “5–65 cases each” treats 65 claim labels as 65 cases. The retrieval
relevance labels were also reviewed by Codex, but the narrative does not disclose
that plainly.

**Remediation:** Describe dataset sizes without combining cases and labels. Add one
short sentence saying that Codex reviewed the passage labels.

**Complete when:** Every dataset count names its unit, and the relevance-review
method is stated once without extended caveat language.

### 5. Remove smaller stale or overstated descriptions

Update the narrative so that it:

- describes the instruction stack as the skill, search-request rules, and corpus
  guide rather than “one versioned skill file”;
- says retrieval and trace evaluations read different recorded artifacts rather than
  claiming every evaluation reads turn traces;
- defines `diagnostic_evidence` as book evidence used to support a diagnosis, not as
  retrieval reading the business's own economics;
- presents the OpenAI Agents SDK as one possible hosted implementation, not a selected
  architecture that has already been justified;
- replaces “nine golden datasets” with a description that does not rely on an
  ambiguous count;
- removes reader-facing `SourceNeed` and query-variant terminology except where a
  short historical note is necessary to explain an unfinished migration;
- keeps old results clearly labeled as historical controls rather than current
  product evidence.

## Priority 2 — Make query-generation inputs match the runtime — Complete

**Problem:** The query-generation experiment exposed the question plus the normal
business fields and, for the guided condition, the corpus guide. It deliberately
excluded `advisor_state` and `field_sources`. The runtime `session start` response,
however, exposes `likely_retrieval_subjects` and `retrieval_query_terms`. An operating
agent can therefore see deterministic query hints that the tested query writers did
not see.

**Status:** Completed on 2026-08-12. The legacy fields still load from old snapshots
for compatibility, but they are no longer computed, serialized, returned by
`snapshot`, or included in the `session start` workbench. Regression tests cover both
fresh and legacy snapshot payloads.

**Recommended remediation:** Remove those legacy retrieval hints from the active
agent workbench. Keep the business facts, readiness, and missing-field information.
The selected method should generate its query from the user question, relevant saved
business facts, and versioned corpus guide—the inputs actually tested.

**Alternative:** If the hints remain part of the intended product, add them to every
model-generated experimental condition and rerun query generation. Do not claim the
existing comparison validates that different input contract.

**Complete when:**

1. The intended query-writer input is documented in one place.
2. Runtime-visible inputs match the winning experimental condition.
3. A regression test prevents legacy retrieval hints from silently re-entering the
   query-writer context.

## Priority 3 — Revalidate the complete retrieval matrix on active chunks — Complete

**Problem:** The query approach × query model × retriever table used heading-aware
chunks. Framework-aware chunks later became the runtime default after a hybrid-only
chunking revalidation. We therefore know that framework-aware works well with the
selected hybrid condition, but we have not replayed the complete BM25-versus-hybrid
matrix on the final chunk boundaries.

**Status:** Completed on 2026-08-12. All ten conditions were replayed from frozen
queries over framework-aware chunks. The boundary audit reviewed 115 case-passage
pairs that had not appeared in the earlier returned heading pool and every weak-overlap
positive. It produced 12 false-negative corrections and one false-positive correction.
The final report is `evals/reports/active_framework_retrieval_matrix.md`.

Corpus guidance remains the best approach under both models and retrievers. Hybrid
preserves 100% Hit@5 and improves Useful@5 over BM25 for both guided writers, so the
active retriever remains hybrid.

**Remediation:** Keep all saved queries frozen and replay these conditions over
framework-aware chunks:

- raw question through BM25 and hybrid;
- unguided `gpt-5.5` through BM25 and hybrid;
- unguided `gpt-5.4-mini` through BM25 and hybrid;
- corpus-guided `gpt-5.5` through BM25 and hybrid;
- corpus-guided `gpt-5.4-mini` through BM25 and hybrid.

For new framework-aware boundaries, transfer labels by source span and review returned
passages for missed valid results or labels that are too broad. Do not regenerate the
queries.

**Complete when:**

1. One report records Hit@1, Hit@3, Hit@5, mean first-useful rank, Useful@5, and
   Noise@5 for all ten conditions on framework-aware chunks.
2. The report records any label corrections and applies them across every condition.
3. Hybrid is retained only if the active-chunk results still justify it against BM25.
4. The narrative contains one current retrieval table; heading-aware matrix results
   remain only as clearly labeled historical evidence if they are retained at all.

## Priority 4 — Reconcile and simplify the narrative — Rendered verification open

**Status:** The factual reconciliation completed on 2026-08-12. A deletion-first
content pass completed on 2026-08-13. It removed repeated conclusions, development-log
material, the job-description appendix, and claims not established by the current
implementation or evidence. The HTML structure, internal anchors, and whitespace pass
validation. The content pass is complete; the final rendered read-through is tracked
as Priority 5 item 14.

A second whole-document pass on 2026-08-13 removed vague maturity disclaimers and
replaced abstract limitations with their concrete consequences. It also corrected two
implementation overclaims: stored file hashes are not currently used to mark facts
stale, and citation validation proves only that an ID appears in the recorded inspected
set—not that the agent read the passage or that it supports the answer.

### 2026-08-13 content-audit inventory

#### Likely delete

**Resolution:** Completed on 2026-08-13.

- The Objective sentence that says the project is a portfolio demonstration. The
  evidence should demonstrate engineering judgment without announcing it.
- The Objective claim that the local CLI makes design choices cheap to test. It is a
  generic justification rather than evidence.
- The Scope sentence claiming that retrieval features were tested rather than assumed
  and that features which did not earn their cost were rejected. The experiment
  sections already show this.
- Repeated architecture slogans outside the primary architecture explanation,
  including the workflow restatement that the agent owns judgment and the deterministic
  core owns state.
- Generic process claims such as failures driving instruction changes and current
  tests being more realistic. Keep the concrete methodology and regression evidence.
- The claim that V1 stores only what is needed for the current decision unless that
  minimality has actually been established.
- The Design subsection that announces query generation as measured and selected.
  Section 3.3 already contains the experiment and decision.
- Speculation about replacing the Pinecone REST client with an official SDK.
- Prose under query retrieval and orchestration that merely restates table values.
- The orchestration cost sentence that repeats the deterministic-core design without
  providing cost evidence.
- The unquantified statement that misses cluster around particular behaviors.
- Development-log anecdotes in the regression section, including path plumbing,
  command-design history, and obsolete query-variant history. Preserve useful history
  in progress documents, not the main narrative.
- The Limits sentence that describes 65 claim labels across 32 cases.
- The job-description mapping appendix. Keep role mapping in
  `JD_REQUIREMENTS_AUDIT.md` rather than repeating the narrative in resume language.
- The absolute closing claim that every number and design rule has a source artifact.

#### Likely merge or relocate

**Resolution:** Completed on 2026-08-13. The standalone Environment section was
removed. Open implementation work is tracked in Priority 5 rather than narrated as
current product behavior.

- Consolidate repeated architecture declarations into one precise statement: the agent
  makes semantic decisions; the CLI performs deterministic execution.
- Fold the useful facts from the standalone Environment section into Objective, Model,
  or Limits, then remove the standalone section if nothing unique remains.
- Keep the Pinecone latency evidence in Retrieval and track latency optimization in
  Priority 5.
- Remove the unfinished source-event migration from the narrative and track it in
  Priority 5.
- State the model-comparison decision once beside its results; track unresolved model
  routing work in Priority 5.

#### Verify before keeping or rewriting

**Resolution:** Completed on 2026-08-13. The active one-search-per-job rule was retained
after verification against the operating skill and CLI contract. Subject metadata was
reduced to its namespace-experiment role. The memory merge-behavior claim was removed
because the current implementation does not enforce the documented policy. The
  chunking criterion was reframed as the role of the early screen, cumulative audit
  totals were replaced with the final-boundary audit, and the regression section now
  states only current coverage.

- Replace the absolute claim that the agent makes every judgment call and the core does
  everything else with the actual semantic-versus-deterministic boundary.
- Correct the claim that every snapshot field records provenance. Provenance applies to
  accepted business facts, not necessarily computed or status fields.
- Verify that the implementation enforces the stated memory merge rules, including
  evidence priority and conflict preservation.
- Decide whether subject labels and the intent taxonomy have enough active product value
  to warrant their current prominence now that retrieval is unfiltered.
- Keep the one-search-per-job rule only if it is an active, tested instruction.
- Verify whether 100% Hit@5 was a predefined chunking acceptance criterion or a rule
  inferred from the observed results.
- Reconsider the cumulative false-positive and false-negative totals. Aggregating
  successive audits and changed chunk boundaries may obscure the quality of the current
  reference set; the latest audit scope and corrections may be more informative.
- Remove the Pinecone decision's reference to avoiding retrieval fanout and ensure the
  decision states only what the latency experiment established.
- Either rebuild the regression section around actual suites, gates, and concrete
  failures or retitle/reduce it; the current section is mostly project history.

#### Preserve as the narrative's evidence spine

- The product definition and scope.
- The workflow and component map.
- Concrete tool boundaries, snapshot schema, guardrails, and trace structure.
- The staged evaluation sequence and metric definitions.
- The early chunking screen and final connected-choice revalidation.
- The current unified retrieval results table.
- The Pinecone latency and namespace experiments.
- The orchestration comparison.

**Editing rule:** Work deletion-first. Remove material that contributes no unique
fact, reasoning, or decision before polishing the sentences that remain. Review the
proposed deletions and substantive rewrites with the user before applying them.

The narrative now keeps the 32-case BM25 chunking screen as an early screen, uses the
46-case framework-aware matrix for the current retrieval decision, and avoids repeating
table results unless the prose adds a decision. The narrative pass is complete; the
remaining implementation, evaluation, and cross-document work belongs in Priority 5.

On 2026-08-17, each quantitative evidence block received a default-closed,
human-readable case table with filtering, sorting, and expandable row details. The
tables are generated from canonical artifacts by
`scripts/render_narrative_evidence.py`; `--check` fails if they drift. Direct links to
the machine-readable files and reports remain available in every panel.

## Priority 5 — Implementation and evidence parity backlog — Open

This is the canonical to-do list for known incompleteness. Removing an unfinished
item from `narrative.html` does not resolve it; the item stays here until the product
decision, implementation, tests, and documentation agree.

An item is complete only when:

1. the intended behavior is explicit;
2. the runtime implements that behavior, or the design explicitly rejects it;
3. regression coverage proves the implemented contract;
4. `DESIGN.md`, `CLI_DESIGN.md`, `BUSINESS_SNAPSHOT_V1.md`, `GOLDEN_DATASET.md`,
   `README.md`, the advisor skill, and `narrative.html` agree where relevant; and
5. the narrative mentions the result only after those conditions are satisfied.

### Contract mismatches — resolve first

1. **Source-event regression migration — Complete (2026-08-13)**
   - Migrated the cases, capture flow, runner, scorer, tests, and report to the
     current one-query `SearchRequest` contract.
   - Six isolated blind runs pass 6/6 with 7/7 expected events and no extras. Two
     post-run answer-key corrections are disclosed in the report.

2. **File-backed fact invalidation — Complete by contract simplification (2026-08-13)**
   - The canonical contract no longer claims automatic invalidation. The agent
     explicitly accepts updates; file paths and SHA-256 hashes record provenance.
   - `snapshot set --source-type file --source <path>` implements that provenance,
     restricts the source to the business directory, and has regression coverage.

3. **Snapshot merge and conflict policy — Complete by contract simplification (2026-08-13)**
   - V1 now specifies explicit updates: the agent resolves ambiguity before writing,
     `snapshot set` overwrites the accepted value and its provenance, and calculated
     fields recompute. There is no hidden source-priority merge engine.

4. **Calculation verification — Complete (2026-08-13)**
   - One formula dispatcher now serves both `calculate` and trace validation.
     `session finish` rejects unknown metrics, invalid inputs, non-finite values, and
     mismatched results. Focused unit and CLI tests pass.

### Product decisions and implementation work

5. **Agent and query-writer model routing — Complete by design decision (2026-08-13)**
   - On the balanced 48-case search-gate suite, `gpt-5.5` scored 48/48: all 24
     required searches found and all 24 prohibited searches avoided. Mini scored
     47/48: 23/24 required searches found and all 24 prohibited searches avoided.
     Mini's one false negative was audited; no gold-label correction was warranted.
   - Keep `gpt-5.5` as the operating agent. The comparison used the current skill,
     CLI, and `SearchRequest` contract rather than the retired SourceNeed interface.
   - Query writing remains part of the operating agent turn. A separate Mini call
     would add latency, another failure boundary, and an API dependency without a
     measured end-to-end benefit.
   - `gpt-5.4-mini` remains a validated bounded query-writer option: it reached useful
     evidence within five hybrid results on all 46 cases. It can be reconsidered when
     deployment has metered model calls and a real cost/latency comparison.

6. **Hosted retrieval latency — Complete (2026-08-13)**
   - Profiling found a redundant 10x vector over-fetch: hybrid consumed 25 candidates
     while Pinecone returned 250 from a 204-chunk corpus.
   - Removing it preserved all 46 top-five lists and reduced sequential latency from
     4.07s p50 / 7.64s p95 to 0.89s / 1.14s. Tail monitoring remains normal
     operational work, not an implementation mismatch.

7. **Semantic citation support — Complete (expanded 2026-08-16)**
   - Audited 20 current-path answers claim by claim against saved business facts,
     deterministic events, and exact cited passages. Current result: 22/22 material
     claims supported across five business contexts.
   - Answer hashes prevent changed text from inheriting a stale audit. Codex is the
     single semantic reviewer, which the report states explicitly.

### Evaluation gaps

8. **Embedding-model selection — Complete (2026-08-13)**
   - A predefined rule compared Small with Large at the deployable 1,536 dimensions
     on the 46 frozen queries. Large preserved 100% Hit@5, raised Useful@5 from 78.7%
     to 86.5%, and reduced Noise@5 from 21.3% to 13.5%; estimated uncached corpus plus
     query cost was $0.017 versus $0.003.
   - All 39 new local case-passage pairs were audited. Large is now the runtime
     default, its cache/vector identity includes dimensions, and 204 chunks were
     indexed in an isolated Pinecone namespace. Hosted replay reached 86.1% Useful@5
     at 1.13s p50 / 1.43s p95.

9. **End-to-end answer quality — Complete (expanded 2026-08-16)**
   - Twenty blind current-path cases now score business-fact accuracy, calculations,
     book application, usefulness, restraint, and claim support. The frozen baseline
     passed 16/20 after the earlier six-case audit had passed 6/6. All source-grounded
     and calculation cases passed; four clarification cases exposed one shared
     input-sufficiency defect: the advisor withheld an immediate decision but promised
     a later result without requesting every material economic input.
   - The fix established a general rule: answer when missing information cannot
     materially change the recommendation; clarify when it can. Domain rules now
     distinguish required inputs from helpful context and conditionally request the
     inputs needed by multi-month payback and downstream-value branches. This was a
     runtime/runbook correction, not four case-specific answer patches.
   - Fresh final runs pass 20/20 with 22/22 material claims supported. The full unit
     suite and relevant evaluations pass, and the final audit is now covered by a
     hash-bound regression test. Both baseline and final reports remain in
     `evals/reports/`.

10. **Golden-dataset breadth — Complete for portfolio scope (2026-08-16)**
    - Expanded answer quality to four cases in each of five materially different
      business contexts, reusing realistic turns from the balanced 48-case suite.
      The 20 cases include 10 source-grounded answers, five calculations, and five
      clarifications. Future observed failures should still become regressions.

11. **Stable regression gate — Complete (2026-08-17)**
    - `python3 scripts/regression_gate.py` runs the unit suite, local retrieval
      smoke test, strict saved-artifact scorers for tool use, source events,
      calculations, and answer quality, the narrative evidence drift check, and
      `git diff --check`.
    - The tool-use, source-event, and answer-quality scorers expose an explicit
      `--require-all-pass` mode so the gate fails on missing or failed results rather
      than merely regenerating a report successfully.
    - Acting-model runs, embedding calls, and hosted retrieval replays remain outside
      the gate; it is deterministic and offline.

12. **Comparable cost reporting — Deferred**
    - If the agent moves from subscription harnesses to metered model calls, record
      billed cost per case alongside quality, latency, and failure mode.

### Cross-document reconciliation

13. **Remove stale current-state claims outside the narrative — Complete (2026-08-14)**
   - `DESIGN.md`, `CLI_DESIGN.md`, `IMPLEMENTATION_PLAN.md`, `GOLDEN_DATASET.md`, the
     README, and the report index now point to the current source-event contract and
     current Pinecone result. Retired source-need material is labeled historical.
   - The retrieval revalidation harness pins its historical Small-embedding controls;
     changing the runtime embedding default cannot silently rewrite that evidence.
   - A second reconciliation replaced stale Claude/model-routing, BM25-default,
     embedding-selection, and unfinished-work claims in the current README,
     architecture, design, JD audit, CLI design, and open-items tracker.

14. **Final narrative and document reconciliation — Source work complete; manual visual pass open (2026-08-17)**
   - Resolved: correct the workflow diagram so inspection can loop within a turn while a
     clarification ends the turn and resumes only after the user responds.
   - Resolved: expand the evaluation-framework and scoring explanations to cover the later
     search-decision, calculation-trace, and answer-quality evaluations—not only the
     action and retrieval suites.
   - Resolved: add the stable eight-check offline regression gate to the regression-coverage
     section.
   - Resolved: state the embedding decision explicitly: use `text-embedding-3-large` at 1,536
     dimensions.
   - Resolved: add the measured Pinecone candidate-depth latency improvement: 4.07s / 7.64s
     p50 / p95 before and 0.89s / 1.14s after, with all 46 top-five lists preserved.
   - Resolved: correct the final answer-quality report and scorer template: the committed
     evidence preserves the failed baseline and final run, not the uncommitted
     intermediate scratch runs.
   - Resolved: reconcile `QUERY_GENERATION_TESTING_DESIGN.md`, which said model selection
     was open, and `IMPLEMENTATION_PLAN.md`, which described a six-answer audit.
   - Open: finish with a rendered visual pass. Automated inspection of the local
     `file://` page is blocked by the in-app browser security policy, so this final
     layout check must be performed manually unless the page is served over HTTP.

## Order of remaining work

1. Complete the remaining manual visual check in item 14. The source changes pass the
   full regression gate.
2. Report comparable metered cost only when the deployment path exposes it.
3. After each item, run its focused regression and reconcile every affected document
   before adding the result to the narrative.
