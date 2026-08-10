# Query Generation Testing Design

**Date:** 2026-08-10
**Status:** Guided v2 clears the development gate; holdout review and final comparison remain open.

## Purpose

This document defines how the project will decide how to generate source-material
search queries. It is intentionally upstream of implementation choices such as
subject filters, multi-query retrieval, namespaces, and rerankers. Those mechanisms
should be introduced only if a measured failure gives the project a reason to test
them.

The research question is:

> Given a search-worthy user question and realistic saved business context, what
> query-generation method most reliably retrieves Money Models passages that answer
> the question?

Model selection is part of that decision, but it is not the whole decision. The
experiment must first compare different ways of constructing a query, then determine
which model tier can execute the winning method reliably.

## Decisions That Precede The Experiment

The golden dataset and relevance labels must exist before experimental results are
generated. Retrieved output from a candidate method must not be used to create that
method's answer key.

The initial dataset contains only turns for which source-material search is already
appropriate. Deciding whether to search is a separate product behavior and is not part
of this query-generation experiment.

The initial experiment does not depend on prior-session retrieval. The current product
returns the most recent session summaries, not sessions selected by relevance. Adding
prior turns would therefore mix query generation with an unvalidated memory-selection
problem.

The evaluator must run retrieval through the real CLI. It may prepare cases, invoke a
generator, invoke the CLI, and score returned chunk IDs, but it must not implement a
second retrieval or ranking path.

## Current Evidence And Gaps

The repository already has useful retrieval evidence, but it does not yet answer the
research question in this document:

- `evals/advisor_search_query_cases.jsonl` contains 30 search-appropriate cases with
  known-useful chunk labels.
- `evals/advisor_query_variants_v2.jsonl` contains a frozen set of query variants, but
  it does not record which model or process generated them.
- Existing query-quality runs show that this frozen variant set performs well with
  hybrid retrieval, but the production CLI does not execute the same cross-variant
  fusion path used by the evaluator.
- Existing query-quality cases supply reviewer-selected subjects and focus terms to
  the query builder. They therefore test retrieval conditional on those semantic
  choices, not whether a generator can make the choices from realistic product input.
- Existing model-routing runs evaluate search decisions and parts of the structured
  search request, but they do not score generated query text by downstream retrieval
  quality.

Accordingly, the existing 30 cases are development evidence. They are not an untouched
holdout for choosing a query-generation method or model.

## Recorded Development Run — 2026-08-10

The first run reused the 30 existing exposed search-query examples. For each example,
the runner replaced the search string with the output of each candidate method, invoked
the public CLI with no subject filter, and compared the returned chunk IDs with the
case's existing known-useful chunk labels. Reference queries, reviewer focus terms,
expected subjects, and useful chunk IDs were not shown to the generators.

The unguided condition means the model received the normal `BusinessSnapshot` but no
additional corpus guide. It does not mean the model had no prior knowledge or that the
snapshot's field names carried no meaning.

All 90 query-generation artifacts were valid and were frozen before retrieval scoring:

| Method | Valid | Mean generation latency | Codex-reported tokens |
|---|---:|---:|---:|
| Raw question | 30 / 30 | 0 ms | 0 |
| Unguided model rewrite | 30 / 30 | 9,762.3 ms | 95,253 |
| Guided model rewrite | 30 / 30 | 8,455.1 ms | 174,530 |

The complete BM25 control produced:

| Method | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw question | 46.7% | 66.7% | 76.7% | 1.739 |
| Unguided model rewrite | 53.3% | 73.3% | 90.0% | 1.889 |
| Guided model rewrite | 66.7% | 90.0% | 96.7% | 1.517 |

The complete hybrid comparison produced:

| Method | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| Raw question | 66.7% | 86.7% | 90.0% | 1.407 |
| Unguided model rewrite | 66.7% | 93.3% | 96.7% | 1.448 |
| Guided model rewrite | 76.7% | 93.3% | 93.3% | 1.179 |

The guided method ranked useful evidence first most often and had the best mean first
useful rank. The unguided method had the best Hit@5, missing one case versus two for
the guided method. This exposed development comparison therefore does not establish a
single winner: failure analysis may inform one general, versioned refinement, but the
final choice must be made on the reviewed holdout.

### Relationship to the pre-existing variant result

The earlier narrative reports 96.7% Hit@1 and 100.0% Hit@3/Hit@5 for local
hybrid retrieval with three frozen query variants plus a deterministic fallback. On
the same enriched 30-case labels, the direct numerical comparison is:

| Condition | Hit@1 | Hit@3 | Hit@5 |
|---|---:|---:|---:|
| Earlier hybrid + three fixed variants + fallback | 96.7% | 100.0% | 100.0% |
| Raw user question + hybrid | 66.7% | 86.7% | 90.0% |
| Unguided single rewrite + hybrid | 66.7% | 93.3% | 96.7% |
| Guided single rewrite + hybrid | 76.7% | 93.3% | 93.3% |
| Guided v2 single rewrite + hybrid | 93.3% | 96.7% | 100.0% |

The earlier condition is numerically stronger, but it is not a valid head-to-head
query-generation result. It begins after reviewer-selected `focus_terms` and
`expected_subjects` have been supplied; the expected subjects are also applied as
retrieval metadata filters. It runs four searches and fuses them. Its three saved
variants have no recorded generating model, prompt, or raw response. The current
experiment starts from the user question and normal saved snapshot, hides reviewer
labels, applies no subject filter, and runs one search.

The defensible interpretation is therefore that the older run establishes a
downstream, information-assisted retrieval ceiling and provides a reason to test
multi-query generation fairly. It does not establish that the product can generate
those variants or subject choices. The six cases completed after the interrupted run
also do not explain the aggregate gap: guided single-query retrieval placed useful
evidence first on all six, while the old condition did so on five of six. Across all
30 cases, the old condition tied the guided method on 21, ranked better on six, missed
none where guided missed two, and ranked worse on one.

### Recorded guided v2 development refinement — 2026-08-10

The v2 prompt was committed as `query-generation-prompt.v2` before generation. It
kept the same input, guide, `gpt-5.5` harness, output contract, no-filter retrieval
path, and 30 exposed cases. Its only intended behavior change was to preserve every
concept necessary to the user's information need while treating the corpus guide as a
translation reference rather than a checklist.

All 30 outputs were valid. The complete result was:

| Backend | Hit@1 | Hit@3 | Hit@5 | Mean first useful rank |
|---|---:|---:|---:|---:|
| BM25 | 86.7% | 96.7% | 96.7% | 1.103 |
| Hybrid | 93.3% | 96.7% | 100.0% | 1.133 |

After the method-neutral label sanity check, hybrid v2 ties guided v1 on 24 cases,
improves four existing ranks, repairs both v1 top-five misses, and regresses none.
Case 010 moved from a top-five miss to rank 1. Case 020 moved from a miss to rank 4 and
is the only v2 case outside the top three. V2 therefore clears the predeclared 22/30
Hit@1, 28/30 Hit@3, and 29/30 Hit@5 development frontier. It becomes a holdout
finalist, not a production choice.

Compared with the older information-assisted four-query ceiling, v2 closes much of
the gap while using one query and no subject filter: 93.3% versus 96.7% Hit@1, 96.7%
versus 100.0% Hit@3, and an equal 100.0% Hit@5. That remaining comparison still does
not isolate query count because the old condition also receives reviewer fields.

The results and case artifacts are preserved in:

- `evals/reports/query_generation_methods_dev.md`
- `evals/reports/query_generation_methods_dev_summary.json`
- `evals/reports/query_generation_methods_dev_cases.jsonl`
- `evals/runs/query_generation/v1/`
- `evals/reports/query_generation_guided_v2_dev.md`
- `evals/reports/query_generation_guided_v2_dev_summary.json`
- `evals/reports/query_generation_guided_v2_dev_cases.jsonl`
- `evals/reports/query_generation_guided_v2_label_audit.md`
- `evals/runs/query_generation/v2/`

These are development results, not an adoption decision. The 16-case multi-scenario
holdout at `evals/query_generation/query_generation_holdout_v1.jsonl` remains untouched
by the generators, and its candidate relevance labels require human review before the
holdout can be frozen and opened.

## Experiment Scope

The experiment tests the production question that begins after the system has decided
that source-material search is appropriate:

```text
current user question + saved BusinessSnapshot facts
-> query-generation method
-> one search query
-> CLI retrieval
-> ranked source passages
```

The first experiment produces one query per case. Multiple-query generation is not
assumed. It becomes a later candidate only if single-query failure analysis supplies a
specific reason to test it.

The first experiment applies no subject filter and selects no subject namespace. This
prevents an unvalidated classifier from hiding or creating query-generation failures.
Subject filtering can be evaluated separately if unfiltered results demonstrate a
repeatable wrong-subject problem.

The following are out of scope for the initial experiment:

- whether source search should happen
- prior-session relevance or memory retrieval
- physical subject namespaces
- cross-encoder or LLM reranking
- answer composition after retrieval
- multi-query fanout

## Corpus-Derived Asset

The guided generation method uses one combined corpus guide. The book's vocabulary and
its frameworks belong together: framework names are useful only when the generator can
also understand their aliases, concepts, and relationships.

The guide should be derived from the source corpus and reviewed for source accuracy. A
compact entry may contain:

- the canonical concept or framework name
- aliases, synonymous phrases, and acronym expansions
- a plain-language description of what the concept explains or when it is useful
- important relationships to other concepts
- named offer mechanisms and other source-specific terminology

The initial guide should cover the corpus rather than only the topics represented in
the golden dataset. It must not contain case-specific relevance labels, expected
queries, or useful chunk IDs. Its generator-visible form should also omit internal
retrieval addresses that would turn the task into a chunk-ID lookup.

The guide may be improved on the development split, but every change must be versioned.
The guide is frozen before holdout evaluation, and its version is recorded with every
generation run.

## Golden Dataset Design

### Case inputs

Each case contains:

- a realistic current user question
- a valid `BusinessSnapshot` fixture
- an explicit indication in the dataset metadata that source search is appropriate
- a split designation
- hidden challenge tags for analysis

The snapshot may contain whatever facts make the business example coherent and
realistic. It should use the actual snapshot schema rather than a special query-only
context object.

The query generator must not receive:

- prior-session records
- `advisor_state.likely_retrieval_subjects`
- `advisor_state.retrieval_query_terms`
- reviewer-selected subjects or focus terms
- reference queries
- relevant chunk IDs or relevance rationales

The two `advisor_state` fields are excluded because they encode parts of the existing,
unvalidated query policy. Supplying them would contaminate the comparison.

### Relevance labels

Before generation runs begin, reviewers identify the passages that directly answer
each question. Each label should record:

- stable chunk ID
- relevance grade, when more than binary relevance is useful
- a short rationale explaining what the passage supports
- label author and review status

The label set should cover multiple acceptable passages when the corpus contains them.
The scorer should not require generated wording to match a reference query.

### Coverage

The dataset should cover at least these query challenges:

- exact Money Models terminology in the user question
- ordinary language that differs from the book's terminology
- cause-and-effect questions
- comparisons between concepts
- questions whose meaning depends on saved business facts
- questions containing realistic but irrelevant business details
- nearby passages that share vocabulary but do not answer the question

The cases should span more than one business scenario. Scenario diversity is necessary
to prevent one business's vocabulary from becoming an accidental query template.

### Splits

The current 30 query cases may be retained as a development and regression set because
their results and labels have already been inspected.

A new holdout set must be authored and relevance-labeled before candidate methods are
run against it. Candidate prompts and the corpus guide may be refined on the development
set. The holdout is opened only after the finalists and decision rules are frozen.

## Query-Generation Methods

### A. Raw question

Use the current user question unchanged as the search query.

Hypothesis: the retriever may already handle realistic language well enough that a
generation step adds no quality worth its latency or complexity.

### B. Simple model rewrite

Give the model the current question and allowed snapshot facts. Ask it to produce one
concise source-search query.

Hypothesis: a model can remove conversational noise and incorporate relevant business
meaning without needing corpus-specific aids.

### C. Model rewrite with the combined corpus guide

Give the model the same question, allowed snapshot facts, and the frozen combined guide.
Ask it to use the guide when relevant to translate the user's language and business
situation into the concepts or relationships the source material uses, then produce one
concise query.

Hypothesis: corpus vocabulary and framework relationships together help the model aim
at the right evidence, especially when the user does not already use the book's terms.

### C2. Guided prompt v2 development challenger — frozen before generation

The first guided development run suggests—but does not prove—that the guide can help
translate ordinary language while also tempting the model to add more neighboring
concepts than the question requires. The v2 challenger tests one general prompt change:
use the guide as a translation reference rather than a checklist.

The prompt does **not** impose a one-concept rule, restrict additional concepts to
comparisons, exclude related concepts as a category, or impose an arbitrary word count.
It instructs the generator to preserve every concept needed for the mechanism,
relationship, comparison, sequence, or combined system in the user's question, while
omitting concepts added only because the guide lists them as related or nearby. The
query should be no longer than necessary without sacrificing essential meaning.

This prompt is versioned as `query-generation-prompt.v2` and must be committed before
its 30 development queries are generated. It receives the same question, snapshot
projection, complete v1 corpus guide, model, output contract, and isolated Codex harness
as guided v1. It is a development challenger, not a holdout finalist by declaration.

For the initial screen, v2 must produce 30 valid outputs with no retrieval execution
errors. To dominate the current single-query frontier, it must achieve at least 22/30
Hit@1 and 28/30 Hit@3 (guided v1) plus 29/30 Hit@5 (unguided v1). Results below that
frontier may still diagnose the prompt hypothesis, but do not earn promotion.

A deterministic keyword-library method is not part of the initial comparison. It would
require designing and maintaining another query system without current evidence that
it addresses a real failure. It remains an optional later diagnostic if the results
create a specific reason to isolate the value of corpus vocabulary from model judgment.

## Minimum Credible Version Of Each Method

The goal before the first run is not to find the best possible prompt. It is to ensure
that all three hypotheses have a fair, competent implementation. The following choices
must be made and frozen for the first recorded development run.

### Shared case input

The raw-question control receives the user's current question unchanged. By definition,
it cannot add snapshot facts that the user did not state in that question.

Both model methods receive the same generator-visible snapshot projection:

- `business`, `money_model`, `economics`, and `problem`
- null and empty values omitted
- `advisor_state` omitted because it contains the current unvalidated retrieval hints
- `field_sources` omitted because provenance does not change what source evidence the
  question requires

This is an end-to-end product comparison, so the model methods' ability to use accepted
business context is part of what they contribute. Context-dependent cases should be
tagged so the report can show whether any gain over the raw question came specifically
from contextualization.

### Shared output contract

The two model methods use the same output contract:

- exactly one non-empty search query
- a short phrase or question intended to find answer-bearing source passages
- no answer, rationale, subject label, namespace, or retrieval filter
- no facts that are absent from the question, allowed snapshot facts, or corpus guide

The runner should reject malformed output rather than silently repair it. The raw
control should preserve the user's wording except for transport-safe whitespace
normalization.

### Prompt pair

The simple rewrite needs a short, general prompt that explains the output contract and
the retrieval goal. It must not include Money Models terminology, worked examples, or
hidden hints that function as an informal corpus guide.

The guided rewrite should use the same base prompt. Its only substantive addition is
the versioned combined corpus guide plus an instruction to use guide concepts only when
they help answer the current question. Keeping the base instructions aligned makes the
guide, rather than unrelated prompt engineering, the meaningful difference between the
two model conditions.

### Corpus-guide shape

Before the guided method is runnable, the project must decide:

- which source-derived entries constitute complete enough corpus coverage
- the fields in each entry and their maximum level of detail
- whether the complete compact guide fits comfortably in the chosen model context
- how source accuracy is reviewed
- the guide's version and freeze process

The initial design should pass the complete compact guide to every case. Selecting a
case-specific subset would introduce another semantic routing system and confound the
first comparison.

### Readiness check

Before retrieval scoring begins, run a small unscored smoke set spanning an exact book
term, a plain-language paraphrase, a context-dependent question, a causal question, and
a noisy question. Inspect only whether:

- the raw control remains unchanged
- both model methods produce one valid query rather than an answer
- both methods use snapshot facts selectively and do not invent facts
- the guided method can use the guide without copying irrelevant terminology into the
  query
- the unguided method was not accidentally given corpus-specific help

This smoke check may repair obvious format or instruction failures. It must not use
retrieval scores to tune a candidate before the first recorded development comparison.
After that first run, general improvements may be developed on the development split,
with every prompt and guide revision preserved. Finalists are frozen before the holdout
is opened.

### Fixed execution settings

The project must also name one capable model and one product-representative harness for
the strategy comparison. Both model methods use the same model version, reasoning or
sampling settings, output parser, and retry policy. Those settings and the prompt
versions are recorded before the first scored run. Model tiers are compared only after
the generation-method comparison has produced a finalist.

## Experimental Controls

### Strategy comparison

Use one capable model for all model-driven methods during the first comparison. This
holds model capability constant while the query-generation method changes.

The two model methods must receive identical case information. The raw control receives
only the unchanged question because the absence of a generation/contextualization step
is the behavior it controls for. Corpus-derived information is allowed only in the
guided condition.

### Retrieval comparison

Run every generated query through the CLI with the backend named explicitly. At minimum,
compare:

- BM25 as the lexical control
- hybrid as the current production candidate

Results must be interpreted within backend. Adding canonical corpus terms may help BM25
more than hybrid; a natural or relational query may behave differently with vector
search. The experiment should reveal this interaction rather than allow the CLI default
to choose the backend silently.

### Model comparison

After the strongest generation method or small set of finalists is selected on the
development cases, compare model tiers using the same method, inputs, corpus assets,
CLI path, and scorer.

The initial OpenAI comparison should include:

- `gpt-5.4-mini`
- `gpt-5.5`

Additional providers should be added only if the result can change a real hosting,
quality, or cost decision.

### Repeated runs

Use a single run to screen clearly weak conditions. Repeat credible finalists before
making a model or strategy decision so that a lucky generation is not mistaken for a
stable result. The number of repeats must be declared before the holdout is opened.

## CLI-Centered Execution

For each case and generation condition, the runner should:

1. Load the user question and allowed snapshot facts.
2. Produce exactly one query using the named method.
3. Save the raw generation request and response or deterministic program output.
4. Invoke the real CLI search command with the query and backend explicit.
5. Save the complete CLI JSON response.
6. Score returned chunk IDs against the frozen relevance labels.

Conceptually, retrieval should be executed as:

```bash
PYTHONPATH=src python3 -m money_model_architect.cli search \
  "<generated query>" \
  --backend <bm25-or-hybrid> \
  --top-k 5
```

The initial test should not pass `--subject`. The eval runner should not call a private
retrieval implementation that behaves differently from this CLI path.

Unit tests may continue to call Python functions directly. Golden-dataset product
evaluation should exercise the CLI contract.

## Scoring

### Primary quality measures

- Useful passage in the top 5: did retrieval return at least one passage that directly
  answers the question?
- Rank of the first useful passage: how much evidence must the agent inspect before
  finding support?

### Secondary measures

- Useful passage at rank 1
- Number of useful passages in the top 5
- Invalid or empty generated queries
- Duplicate queries across materially different cases
- Query-generation latency
- Retrieval latency
- Model token or cost proxy
- Failure category by challenge tag

If graded relevance labels are available, report a graded top-5 ranking metric in
addition to the plain, human-readable measures above. It should not replace the case
table and failure analysis.

## Decision Rules

The project should prefer the simplest method that preserves retrieval quality.

- If raw questions match the generated approaches, do not add query generation.
- If a simple rewrite wins, do not add a corpus-guide dependency.
- If the guided rewrite wins, retain one combined guide and compare model tiers using
  that frozen guide. Use the cheapest tier that preserves the result.
- If the guide helps only a narrow challenge category, decide whether that measured
  benefit justifies sending it on every search before adopting it.
- If one method wins only on BM25 and another is more robust on hybrid, make the query
  method and retrieval-backend decision together.
- If all query methods fail on the same passages, investigate chunking, corpus labels,
  or retrieval rather than adding query-generation complexity.

No method is promoted solely because it sounds more sophisticated or resembles a
common RAG pattern.

## Required Artifacts

Every experiment should preserve:

- dataset version and split
- snapshot fixture version
- query-generation method and version
- prompt text, when a model is used
- model and harness identity
- combined corpus-guide version, when used
- raw generated query
- explicit CLI command configuration
- CLI output and returned chunk IDs
- scorer version
- aggregate report and case-level results
- recorded decision, including non-adoptions

## Implementation Sequence

1. Inventory the existing corpus index, framework summary, glossary material, and
   decision trees as inputs to one combined guide.
2. Define the generator-visible snapshot projection without retrieval hints.
3. Convert the current 30 exposed cases into an explicit development/regression set.
4. Author and freeze a new multi-scenario holdout with independent relevance labels.
5. Build and review the first compact, full-corpus guide.
6. Write the shared base prompt and the guided extension, then freeze model and harness
   settings for the first run.
7. Implement the three named generation methods behind one small experimental interface.
8. Run the unscored readiness check and fix only validity or instruction failures.
9. Make the eval runner invoke the CLI with an explicit backend and save complete artifacts.
10. Run the strategy comparison on development cases with one capable model.
11. Analyze failures and version any general prompt or guide improvements on development cases.
12. Freeze the finalist methods, prompts, guide, repeat count, and decision threshold.
13. Compare model tiers on the finalists, then open the untouched holdout.
14. Record the selected method or the decision that no generation method earned adoption.
15. Reconcile the CLI default, operating instructions, tests, and narrative with the measured decision.

## Completion Criteria

The query-generation design is considered decided when:

- the dataset and holdout were labeled before candidate results were inspected
- every candidate ran through the same CLI retrieval path
- generation strategy was compared independently of model tier
- model tier was compared on a frozen strategy
- retrieval backend was explicit rather than inherited from a default
- quality, latency, usage, and case-level failures were recorded
- the simplest method meeting the declared quality bar was selected
- unsupported mechanisms remained out of the production path
