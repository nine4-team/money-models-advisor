# Narrative Accuracy and Structure Audit

**Created:** 2026-08-17

This document records the error patterns identified while reviewing the design
section of `narrative.html` and defines the method for auditing the rest of the
narrative. This is an accuracy and information-architecture audit, not a generic
prose-tightening pass.

## Error patterns already identified

### 1. Incorrect categorization

The corpus guide was placed under Instructions because the instructions reference
it. That categorized it by where it is consumed rather than what it is. The guide
is derived knowledge about the corpus and belongs under Knowledge and Retrieval.

### 2. Overview/detail duplication

The full Instructions section repeated the overview card instead of explaining the
underlying components, responsibilities, boundaries, and rationale. A detail section
must add meaningful information rather than restating its label.

### 3. Collapsed architectural boundaries

Operating rules, search policy, and corpus metadata were described as one
"instruction stack" even though they have different purposes:

- operating rules govern the complete advisor turn;
- search-request rules govern when and how the agent searches;
- the corpus guide describes concepts and relationships in the knowledge source.

### 4. Documentation/runtime drift

The selected runtime uses the corpus guide, but the guide still labeled itself
`candidate`. Labels such as `active`, `selected`, `default`, `tested`, and
`historical` must match the current implementation and artifacts.

### 5. Vague technical shorthand

"The agent interprets these rules and makes the semantic decision" hid concrete
behavior behind an abstract phrase. The actual behavior is that the agent applies
the rules to the current situation and decides whether to clarify, inspect business
context, calculate, search, or answer.

### 6. False singular or false unity

"The semantic decision" implied one identifiable decision where the agent actually
chooses among several actions and makes additional context-dependent judgments.
Descriptions must not collapse multiple decisions or mechanisms into one vague noun.

### 7. Description without justification

The original section listed what existed without explaining why the instructions
are separated or why the agent/CLI responsibility boundary is designed that way.
Important architectural descriptions must explain the reason for the boundary, not
only name its parts.

## Audit questions

Apply these checks to every overview card and narrative section.

| Check | Question |
|---|---|
| Category | Is the component grouped according to what it actually is rather than where it happens to be used? |
| Concrete meaning | Can every abstract phrase be translated into observable behavior? |
| Overview versus detail | Does the detailed section add meaningful information beyond the overview? |
| Boundaries | Are distinct responsibilities, artifacts, or mechanisms being collapsed together? |
| Actor | Does the text clearly say whether the agent, CLI, retrieval system, or evaluator performs the work? |
| Current truth | Do names, statuses, defaults, counts, and selected approaches match the repository? |
| Runtime versus evaluation | Is an experimental method being confused with current product behavior? |
| Current versus historical | Is retired evidence presented as if it still defines the system? |
| Rationale | Does the section explain why the design was chosen? |
| Evidence | Is every measured claim supported by the current experiment and canonical report? |
| Necessity | Does the sentence improve understanding, or should it be removed? |

## Language requiring scrutiny

Flag phrases like these for inspection rather than automatically preserving or
deleting them:

- semantic decision
- bounded system
- production-oriented
- intelligent orchestration
- robust
- appropriate
- sufficient
- optimized
- current path
- deterministic where possible
- tested rather than assumed

For each occurrence, ask:

1. What exactly happened?
2. Who or what performed the action?
3. What observable behavior or artifact does the phrase describe?
4. Is the claim necessary here?

## Audit workflow

1. Establish the current implementation and canonical evidence as the source of
   truth.
2. Audit the entire narrative without editing it.
3. Produce a section-by-section issue inventory containing the quoted language,
   issue type, explanation, and source-of-truth comparison.
4. Classify each issue as `delete`, `move`, `rewrite`, `substantiate`, or
   `reconcile with implementation`.
5. Review the inventory before making narrative changes.
6. Apply the approved structural and factual changes.
7. Run a second pass for remaining vague language and overview/detail repetition.
8. Verify every quantitative and architectural claim against the repository.
9. Run the regression gate and complete a final rendered-layout review.

## Required output for the inventory

Each finding should contain:

- section number and heading;
- exact quoted text;
- error category;
- why the language is inaccurate, unclear, redundant, or misplaced;
- the relevant source of truth;
- proposed action, without silently making the change.

## Audit inventory — 2026-08-17

This inventory covers the complete visible narrative, its generated evidence panels,
and the repository documents that the narrative names as fuller contracts. No
`narrative.html` changes were made during this audit.

### Verification completed before classification

- `scripts/render_narrative_evidence.py --check` passes, so the generated evidence
  tables match their canonical artifacts.
- All 27 relative links in the narrative resolve.
- The HTML contains no duplicate IDs.
- The frozen scorers still report 24/24 tool-use cases, 6/6 source-event cases,
  5/5 calculation-trace cases, and 20/20 answer-quality cases with 22/22 supported
  material claims.
- The corpus inventory claims are accurate: 32 transcript files, 88,032 words,
  28 corpus-guide entries, and 204 framework-aware chunks.

### Priority A — factual and contract errors

#### A1. The tool count and active tool surface do not agree

- **Section:** 2.5, Tools
- **Quote:** “The CLI emits structured JSON through eight operations”
- **Categories:** current-truth drift; false unity; incomplete component description
- **Problem:** The section creates its own set of eight rows by combining
  `snapshot`/`snapshot set`, including `diagnose` and `index pinecone`, and omitting
  `setup` and the low-level `turn record`. The parser exposes nine top-level commands.
  The operating skill's operation table includes `setup_state` and `turn_record` but
  omits `diagnose`; `session start` advertises seven operations and also omits
  `diagnose`. There is no single defensible set of “eight operations.”
- **Source of truth:** `src/money_model_architect/cli.py` parser and
  `available_operations`; `.codex/skills/money-model-advisor/SKILL.md` Advisor
  Operations table.
- **Action:** `reconcile with implementation`. Decide which commands are normal-turn,
  setup, low-level compatibility, and infrastructure operations. Align the CLI
  workbench and skill first, then describe categories instead of asserting an
  arbitrary total.

#### A2. The guardrails section falsely says only two failures reject a turn

- **Section:** 2.8, Guardrails
- **Quote:** “Two failures reject the turn”
- **Categories:** current-truth drift; collapsed validation boundary
- **Problem:** `session finish` can reject many other structural failures: missing
  messages or actions, unknown action labels, malformed source events, invalid intent,
  an invalid or extra-field `SearchRequest`, a query that differs from the executed
  query, missing inspected chunks, invalid calculation data, and malformed citations.
  Citation provenance and calculation recomputation are two important categories,
  not the only rejecting conditions.
- **Source of truth:** `_normalize_session_finish_record`,
  `_normalize_source_event`, `_validate_search_request_payload`, and
  `_normalize_calculation_event` in `src/money_model_architect/cli.py`.
- **Action:** `rewrite`. Describe the complete structural-validation categories, then
  give citation provenance and calculation recomputation the extra explanation they
  deserve.

#### A3. Advisory status is shown as a guaranteed linear progression

- **Section:** 2.6, Memory
- **Quote:** “moves through four stages: insufficient_context → diagnosable →
  diagnosed → recommendable”
- **Categories:** inaccurate process model; false singular sequence
- **Problem:** The code derives the status from current readiness and whether a
  diagnosed constraint exists. A snapshot can jump to `diagnosed` without first being
  `diagnosable`, and later updates can move it backward. These are states, not a
  monotonic workflow.
- **Source of truth:** `BusinessSnapshot._advisory_status()` in
  `src/money_model_architect/snapshot.py`.
- **Action:** `rewrite`. Present the four possible states and their conditions without
  a one-way arrow.

#### A4. The retrieval overview overstates the hybrid default as universal behavior

- **Section:** 2.7, Knowledge & retrieval
- **Quote:** “Every search ... runs hybrid”
- **Categories:** current-truth drift; absolute language
- **Problem:** The active structured-request path defaults to hybrid, but callers may
  explicitly select BM25 or vector, and raw debug search defaults to BM25. “Every
  search” is false even though hybrid is the selected product default.
- **Source of truth:** `search` argument handling in
  `src/money_model_architect/cli.py`.
- **Action:** `rewrite` as “The active structured-search path defaults to hybrid,” and
  keep manual/debug alternatives out of the main explanation unless needed.

#### A5. The model section generalizes a focused test to all agent decisions

- **Sections:** 2.2 Model card; 2.3, Model
- **Quotes:** “Tests select gpt-5.5 for agent decisions”; “Current tests select
  gpt-5.5 for agent decisions”
- **Categories:** evidence overreach; false scope; vague technical shorthand
- **Problem:** The comparative model test covers the binary search/no-search gate.
  The 20-answer suite demonstrates `gpt-5.5` behavior, but does not compare Mini on
  full next-action selection, calculations, clarification, or answer composition.
  The evidence supports selecting `gpt-5.5` as the operating agent, not claiming a
  comparative win across all “agent decisions.”
- **Source of truth:** `evals/reports/search_decision_model_comparison.md` and
  `evals/reports/advisor_answer_quality_expanded.md`.
- **Action:** `rewrite`. Name the evidence actually used: the search-gate comparison,
  the `gpt-5.5` answer audit, and the separate bounded query-writing comparison.

#### A6. Documents named as fuller contracts contradict the current request shape

- **Sections:** 2.6 and 2.9 references to `BUSINESS_SNAPSHOT_V1.md` and
  `CLI_DESIGN.md`; repository-wide support for the narrative
- **Categories:** documentation/runtime drift; source-of-truth conflict
- **Problem:** `ARCHITECTURE.md` shows an invalid two-field search request containing
  `retrieval_mode`, while the runtime requires exactly `intent`, `user_turn`, and
  `query`. `BUSINESS_SNAPSHOT_V1.md` still shows retired layer-based, multi-query
  session evidence. `CLI_DESIGN.md` says the validator accepts the old multi-query
  shape, but the active validator requires exactly the single requested query. A
  reviewer following the narrative into these files gets contradictory contracts.
- **Source of truth:** `SearchRequest` in
  `src/money_model_architect/advisor_queries.py` and the request validation in
  `src/money_model_architect/cli.py`.
- **Action:** `reconcile with implementation`. Correct the linked contract documents
  before treating the narrative's cross-references as complete.

### Priority B — evaluation and decision-chain gaps

#### B1. The 24-case next-action evidence is characterized inconsistently

- **Sections:** 3.1, Evaluation framework; 3.2, Scoring
- **Quotes:** “A 24-turn suite tests whether the agent chooses the right action”;
  “The reference traces for all 24 tool-use cases validate the action scorer”
- **Categories:** runtime-versus-evaluation confusion; incomplete methodology
- **Problem:** These sentences alternately describe an agent-performance test and a
  scorer-validation fixture. The canonical report says 19 dev/regression traces were
  captured in-thread by Codex and only five scenario-holdout traces used separate
  acting agents after prompt freeze. The 24/24 number is useful as a captured
  regression baseline, but it is not one uniform blind model benchmark.
- **Source of truth:** `evals/reports/advisor_tool_use_judgment.md`.
- **Action:** `rewrite`. State what was run and distinguish the five stronger
  holdout traces without adding a long caveat.

#### B2. The active source-event evaluation is missing from the method story

- **Sections:** 3.1, 3.2, and 3.5
- **Quote:** 3.5 names “source events” among the gate's scorers, but the narrative
  never defines its scoring or reports its result.
- **Categories:** incomplete evaluation framework; asymmetric evidence; missing raw
  data access
- **Problem:** Source-event integrity is a core part of the architecture and an active
  golden suite. Six blind cases pass 6/6 with 7/7 expected events and no extras; two
  answer-key corrections are recorded. Unlike the other active suites, it has no
  scoring row, result summary, or expandable evidence panel in the narrative.
- **Source of truth:** `evals/reports/advisor_source_event_traces.md` and
  `evals/advisor_source_event_cases.jsonl`.
- **Action:** `move` and `substantiate`. Add one compact trace-integrity subsection
  under regression coverage or scoring, with a default-closed generated data panel.

#### B3. The answer-quality scoring definition omits most of the actual rubric

- **Section:** 3.2, Scoring
- **Quote:** “A frozen answer passes when it follows the expected answer,
  calculation, or clarification path and its material claims are supported”
- **Categories:** incomplete definition; collapsed evaluation dimensions
- **Problem:** The audit schema separately checks business-fact accuracy,
  calculation accuracy, reasonable book application, usefulness/responsiveness,
  appropriate restraint, and material-claim support. The narrative reduces that to
  path conformance and support, hiding the method used to produce 20/20.
- **Source of truth:** `evals/answer_quality_audit_schema_v1.json` and
  `scripts/eval_advisor_answer_quality.py`.
- **Action:** `rewrite` with the six compact dimensions.

#### B4. The false-negative/false-positive section does not state its scope clearly

- **Section:** 3.3, False-negative and false-positive check
- **Quote:** “The audit added 12 missing useful labels and removed one overly broad
  label”
- **Categories:** ambiguous aggregation; incomplete quantitative claim
- **Problem:** Those numbers describe only the final framework-boundary audit. The
  canonical query-generation report records 161 missing labels added and 14 broad
  labels removed across all successive retrieval audits. The current heading reads
  like a summary of the whole checking process, while the paragraph silently reports
  only the last stage.
- **Source of truth:** `evals/reports/query_generation_current.md` and
  `evals/reports/active_framework_retrieval_matrix.md`.
- **Action:** `rewrite`. Either narrow the heading to the final-boundary review, or
  state both cumulative and final-stage totals with explicit scopes. Do not combine
  them into an unexplained single error rate.

#### B5. Connected retrieval choices were not replayed after selecting Large embeddings

- **Sections:** 3.3, Chunking; Query generation and retrieval backend; Pinecone
  namespaces; Embedding model
- **Quotes:** the query matrix explicitly holds `text-embedding-3-small` constant;
  the namespace comparison also uses Small; the later embedding experiment changes
  the active vector model to Large.
- **Categories:** unclosed methodology dependency; active-versus-experimental gap
- **Problem:** The final Large experiment tests only the winning framework-aware,
  corpus-guided, hybrid condition. It does not replay the five chunking alternatives,
  the ten query/retriever conditions, or the namespace layouts under the selected
  embedding. The narrative accurately labels the earlier tables, but the combined
  “active path” decision is not fully revalidated after changing a component that can
  alter ranking.
- **Source of truth:** `evals/reports/active_query_chunking_revalidation.md`,
  `evals/reports/active_framework_retrieval_matrix.md`,
  `evals/reports/active_query_pinecone_revalidation.md`, and
  `evals/reports/embedding_model_comparison.md`.
- **Action:** `reconcile with implementation`. Run the smallest connected-choice
  replay needed to confirm the decisions under Large, then update the narrative only
  after the evidence exists.

#### B6. The narrative does not explain why the active query writer is not Mini

- **Sections:** 2.3 and 3.3
- **Quote:** Mini is called “a viable bounded query writer,” while the result table
  gives it the best guided Hit@3, mean first-useful rank, Useful@5, and Noise@5.
- **Categories:** decision without sufficient rationale; result/decision disconnect
- **Problem:** The narrative never explains why query writing remains in the
  `gpt-5.5` operating turn. The canonical design says a separate Mini call adds a
  second latency/failure boundary without measured end-to-end benefit; the query
  report also records that Mini was slower and used more harness-reported tokens.
- **Source of truth:** `DESIGN.md`, `GOLDEN_DATASET.md`, and the query-generation
  model comparison reports.
- **Action:** `substantiate`. Add one concise reason beside the model decision; do not
  add a general model-routing essay.

#### B7. Not every quantitative claim has the requested underlying-data view

- **Sections:** 2.7 and 3.5
- **Quotes:** “32 lesson transcripts ... about 88,000 words”; “versioned 28-entry
  guide”; “204 chunks”; and the unnamed source-event scorer in the eight-check gate.
- **Categories:** incomplete evidence access; inconsistent presentation
- **Problem:** Experimental tables have default-closed, human-readable evidence
  panels, but these inventory/result claims do not. The user requested an inspectable
  view whenever the narrative cites raw quantitative data.
- **Source of truth:** `corpus/transcripts/`,
  `evals/query_generation/corpus_guide_v1.json`, the framework-aware corpus index,
  and `evals/reports/advisor_source_event_traces.md`.
- **Action:** `substantiate`. Add compact generated inventories or direct human-readable
  links; source-event results should receive the same row-level treatment as other
  evaluated cases.

### Priority C — clarity and information architecture

#### C1. The design opening repeats the vague “semantic” shorthand

- **Sections:** Design lede; 2.3, Model
- **Quotes:** “The agent makes semantic decisions”; “supplies semantic judgment”
- **Categories:** vague technical shorthand; false unity
- **Problem:** The wording hides the concrete responsibilities the narrative later
  explains. There is no single categorical semantic decision.
- **Source of truth:** `DESIGN.md` Responsibility boundary and the operating skill.
- **Action:** `rewrite` using the actual choices: clarify, inspect context, calculate,
  search, judge passage usefulness, and compose the answer.

#### C2. The component map groups shared knowledge and cross-cutting controls under execution

- **Section:** 2.2, Component overview
- **Quote:** “Deterministic core — execution” contains Tools, Memory, Knowledge,
  Guardrails, and Observability.
- **Categories:** incorrect categorization; collapsed architectural boundaries
- **Problem:** The corpus and corpus guide are knowledge resources; the agent reads
  the guide and judges passage usefulness. Guardrails span agent rules, CLI
  validation, and semantic audits. Observability spans runtime traces and evaluation
  artifacts. Placing all three under deterministic execution repeats the same
  categorization-by-consumer error previously found in Instructions.
- **Source of truth:** Sections 2.4, 2.7, 2.8, and 2.9 plus `DESIGN.md`.
- **Action:** `move` or `rewrite`. Either introduce a shared-resources/cross-cutting
  zone or label the cards as interfaces rather than claiming they all belong to the
  deterministic core.

#### C3. “Versioned rule sets” implies formal versions that do not exist

- **Sections:** 2.2 Instructions card; 2.4, Instructions
- **Quote:** “two versioned rule sets”
- **Categories:** unsupported precision; documentation/runtime drift
- **Problem:** The corpus guide has an explicit v1 identifier, but neither
  `SKILL.md` nor `search_request_rules.md` declares a version. Git history versions
  every repository file, which is weaker and not what the wording normally implies.
- **Source of truth:** `.codex/skills/money-model-advisor/SKILL.md` and
  `.codex/skills/money-model-advisor/search_request_rules.md`.
- **Action:** `rewrite` as maintained/separate rule sets, or introduce explicit rule
  versions if that is a real contract requirement.

#### C4. The corpus-guide description turns an instruction into a guarantee

- **Sections:** 2.7 and 3.3 Query approaches
- **Quotes:** “translate the user's language ... without losing the relationships”;
  “preserving every concept required by the question”
- **Categories:** description without measured boundary; absolute language
- **Problem:** The rules instruct the model to preserve the full information need,
  and the retrieval experiment shows aggregate improvement. Neither proves that every
  generated query preserves every required relationship or concept.
- **Source of truth:** `search_request_rules.md` and the 46-case retrieval reports.
- **Action:** `rewrite` as intended behavior (“the agent is instructed to ...”) and
  leave measured performance to Section 3.3.

#### C5. The displayed trace example looks empirical but is not tied to a real run

- **Section:** 2.9, Observability
- **Quote:** “A recorded turn — abridged session-finish artifact”
- **Categories:** unsupported example; current-versus-illustrative ambiguity
- **Problem:** The panel has no underlying artifact link, omits the retrieval backend
  used in current source events, and uses a chunk score of `20.4`, which resembles a
  lexical score rather than the active hybrid RRF score. A reader cannot tell whether
  it is a real current-path trace or a schematic payload.
- **Source of truth:** frozen `session_record.json` files under
  `evals/runs/answer_quality/expanded_v1_final/`.
- **Action:** `substantiate` with an abridged real frozen trace, or relabel it clearly
  as a schema example and make its fields consistent with the active contract.

## Recommended resolution order

1. Resolve A1, A2, A3, A4, and A6 against the runtime before editing prose.
2. Decide whether to run the Large-embedding connected-choice replay in B5; this is
   the only finding that requires a new experiment rather than documentation work.
3. Correct the evaluation story in B1 through B4 and add the missing source-event
   evidence panel.
4. Add the concise model-routing rationale in B6 and close the evidence-access gaps
   in B7.
5. Apply the clarity and component-map changes in Priority C.
6. Regenerate evidence panels, run `scripts/regression_gate.py`, and complete the
   manual rendered review.
