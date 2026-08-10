# Narrative Clarity Pass

A section-by-section clarity pass over `narrative.html`. Goal: plain language, no
jargon-without-introduction, no metaphors, no unnamed referents, no filler —
readable cold by someone who hasn't been living in the project.

Process:
1. **Assess** each section's clarity; record the specific problems and a planned
   rewrite here.
2. **Rewrite** each planned section, but only apply it if the rewrite clears the
   bar (plainer AND same meaning/numbers). Record pass/fail.

Reference standard: §3.4 and §3.5 were rewritten to the target voice and approved.
They are the calibration, not up for re-editing.

---

## Calibration example — the approved §3.5 rewrite (before → after)

This is the worked example. Every planned rewrite should be held to this standard.

**BEFORE**

> **One flattened query lost to agent-written variants**
>
> The `searchq_v1_001` miss is what put query variants into the design (§2.4):
>
> - **The case** — The user asks why fulfillment cost matters for paid ads — a causal question.
> - **The diagnosis** — The v1 query builder collapsed the agent's source need into one fixed list of its terms — a reasonable baseline, since it kept agent judgment out of the comparison and gave every eval the same query to score. But a list of nouns loses the cause-and-effect shape of the question, so vector search ranked nearby payback/CAC chunks above the one passage that actually explains gross profit and fulfillment cost. The failure was in how the query was built, not in the retriever.
> - **The fix** — Deliberately constrained — not one freeform agent query, which would trade away traceability. The agent writes 2–4 query variants in a fixed format, the mechanical query stays in the set as a fallback, and all results are merged with reciprocal-rank fusion so no variant can push the fallback out.

**AFTER**

> **Why the agent writes several search queries, not one**
>
> Once the agent decides what to search for, that decision has to become an actual search query. The first version did the simplest thing — take the key terms and run them as one query. It worked on most turns and failed on one clear kind of question (§2.4):
>
> - **The question** — "Why does fulfillment cost matter for whether ads can work?" The user is asking why one thing affects another, not just for a definition.
> - **What went wrong** — The one-query builder just strung the terms together — gross profit, fulfillment cost, CAC, payback. A bare list doesn't say the user wants the link between them, so the search brought back nearby chunks about payback and CAC and ranked the one passage that actually explains the fulfillment-cost-to-gross-profit connection too far down. The right chunk existed; the query just didn't surface it. The problem was the query, not the search engine.
> - **The fix** — Instead of one keyword list, the agent writes two to four short rephrasings of the search. The plain keyword version stays in as a safety net. All of them run, and chunks that keep showing up across the rephrasings rise to the top (reciprocal-rank fusion). Every query is written down, so the search stays auditable — rather than handing the agent one free-form query no one can check.

**What the rewrite did (the moves to copy):**
- **Title names the subject and states the claim**, readable cold: "One flattened query lost to agent-written variants" (which query? lost how?) → "Why the agent writes several search queries, not one."
- **Jargon replaced with plain words**: "collapsed the agent's source need into one fixed list of its terms" → "just strung the terms together"; "a list of nouns loses the cause-and-effect shape" → "a bare list doesn't say the user wants the link between them."
- **The abstract label became the concrete example**: "The case: …a causal question" → the actual question quoted, "Why does fulfillment cost matter for whether ads can work?"
- **Kept the one necessary technical term but glossed it**: "reciprocal-rank fusion" stays, in parentheses, after the plain description ("chunks that keep showing up across the rephrasings rise to the top").
- **Cut the meta-filler**: dropped "a reasonable baseline, since it kept agent judgment out of the comparison and gave every eval the same query to score" and the confusing "trade away traceability."
- **Meaning and every technical fact preserved** — only the language changed.

Status legend: `assess` = assessed, plan recorded · `pass` = rewrite applied ·
`skip` = judged clear, no change.

| Section | Verdict | Rewrite status |
|---|---|---|
| Hero (Objective/Design/Method) | MINOR | pass (2 edits) |
| §1 + §1.1 Scope | MINOR | pass (2 edits) |
| §2.1 Agentic workflow | MINOR | pass (3 edits; edit 2 re-fixed by me) |
| §2.2 Data integration | CLEAR | skip |
| §2.3 Tool use | CLEAR | skip |
| §2.4 RAG pipeline | MINOR | pass (1 edit) |
| §2.5 Observability | CLEAR | skip |
| §3.1 Evaluation framework | MINOR | pass (4 edits) |
| §3.2 Quality scoring | MINOR | pass (4 edits) |
| §3.3 Chunking strategy | CLEAR | skip |
| §3.4 Hybrid retrieval | gold ref | done (approved) |
| §3.5 Query generation | gold ref | done (approved) |
| §3.6 Latency benchmarks | MINOR | pass (title + gloss) |
| §3.7 Pinecone namespaces | MINOR | pass (title states finding + 1 edit) |
| §3.8 Platform selection | MINOR | pass (3 edits) |
| §3.9 Regression detection | MINOR | pass (retitle + intro; list kept as prose) |
| §3.10 Model tiering | CLEAR | skip |
| §4 + JD appendix | MINOR | pass (6 edits inc. nav gist) |

**My assessment of the subagent rewrites (the quality gate):** accepted nearly all
as proposed. Two deviations: §2.1's second edit swapped filler for a mild metaphor
("holds up the rest of the page") and left the "division of labor" category label —
I applied a cleaner version ("This split is what makes the rest work"). §3.9
proposed a `<ul class="rows">` list, but `.rows` only styles `<dl>` and a second
list would sit right above the existing `dl.rows` — so I kept the retitle and the
plain-language "blind" definition but rendered the promotion rule as clean if/then
prose instead of a list. All numbers, cross-references, and HTML structure
preserved; tag balance verified; all ten §3.x sections intact.

---

## Assessments and planned rewrites

### Hero (Objective / Design / Method) — MINOR
Problems: "auditable trace" front-loaded before "trace" is introduced; "judgment
suites scored against agents that never saw the expected answers" compresses too
much for a cold reader; "beat the baseline on a measurement" — "on a measurement"
is filler.
Plan: word-level. Name the trace plainly (a recorded turn you can check) or defer
the term; replace "judgment suites" with "the suites that grade the agent's
judgment"; cut "on a measurement". No structural change.

### §1 + §1.1 Scope — MINOR
Problems: "production RAG infrastructure" used 3× as a category stand-in for the
concrete thing (a vector database, hybrid search, multiple namespaces); "seeded
the golden eval set" — "seeded" is a mild metaphor and "golden eval set" is used
before it's defined in §3.
Plan: replace the "production RAG infrastructure" abstraction with the concrete
components the section already names; swap "seeded" for plain wording and gloss or
defer "golden eval set". No structural change.

### §2.1 Agentic workflow — MINOR
Problems: "and the one everything else follows from" and "is what the rest of the
page depends on" are near-restatement padding; "The CLI shape pays off three ways"
— "shape" is a vague subject.
Plan: cut or concretize the two padding clauses; give "pays off three ways" a
plain subject ("Making the deterministic side a CLI pays off three ways"). Keep
the subscription-vs-API cost reasoning intact — it's precise. Word-level only.

### §2.2 Data integration — CLEAR (skip)
Block-by-block gloss defines every term as it appears; design reasons stay
concrete. Meets the bar.

### §2.3 Tool use — CLEAR (skip)
Each operation states what it does and doesn't do, concretely. No stumbles.

### §2.4 RAG pipeline — MINOR
Problems: RRF called "the reranking step" — loosely named; RRF is a merge of two
ranked lists, and the appositive may confuse a reader who knows reranking as a
separate model stage. "merging by rank sidesteps it" leaves "it" one step removed.
Plan: rename the RRF appositive to what it is (merging the two ranked lists by
position); optionally name what "sidesteps it" sidesteps. Otherwise strong.
Word-level only.

### §2.5 Observability — CLEAR (skip)
Defines "trace" through its concrete contents; ties each rule to the failure it
prevents. Meets the bar.

### §3.1 Evaluation framework — MINOR
Problems: double "so" in the lede, second clause restates the ordering; "retrieval
objective / corpus layers / focus concepts" undefined triplet at first use;
"measure retrieval architecture" is a vague category label; "Self-report never
becomes the metric" is negation-for-punch; "keeping weak evidence visible" is
abstract.
Plan: collapse the double "so"; define the triplet concretely (what to look for,
which layer, which concepts) or drop it; replace "measure retrieval architecture"
with "which method ranks the right passage higher"; flip the self-report line
positive. Keep the table.

### §3.2 Quality scoring — MINOR
Problems: "namespaces" used here before §3.7 defines it (elsewhere the same thing
is "corpus layers" — two names, one thing); "harmless context-loading" jargon;
"keeps each search's retrieval clean" is polished-but-vague ("clean" = ?); decision
box repeats §3.1's "measure retrieval, not tool-use noise".
Plan: use one term (defer "namespace" to §3.7); replace "harmless context-loading"
and "clean" with the literal reason (one search per topic, so each ranks against
only its own passages); trim the decision box so it doesn't echo §3.1.

### §3.3 Chunking strategy — CLEAR (skip)
At the gold-standard bar. Optional nit: "less than half a percent" is applied to an
MRR delta, not a true percentage — leave unless it bothers.

### §3.6 Latency benchmarks — MINOR
Problems: "zero embedding API batches" compressed — a cold reader can't tell it
proves the cache served everything; title buries that the slowness was fixed.
Plan: gloss "zero embedding API batches" (cache served every query, no new
embedding calls); consider a title that carries the fix, not just the exposure.

### §3.7 Pinecone namespaces — MINOR
Problems: title "One namespace or five" names the question but withholds the
finding; "better routing than any production router could promise" leans on an
unintroduced concept; "Latency got worse where it counts" — "where it counts" is
filler (the p95 clause already says where).
Plan: put the finding in the title (splitting cost tail latency, won nothing); cut
"where it counts"; drop or unpack the "production router" aside. Keep the mechanism
paragraph and saturation caveat — they're strong.

### §3.8 Platform selection — MINOR
Problems: title "platform" doesn't signal it means LLM provider; "not 'gpt-5.5 >
Opus'" and "cost lever … architectural, not model choice" are negation-for-punch
with padding lead-ins.
Plan: title names the subject (which LLM provider); replace the negation forms with
the literal points (both clear the bar; the deterministic work stays in the CLI on
either platform, so it's never billed as tokens — a saving independent of provider).
Keep tables/latency/divergence prose.

### §3.9 Regression detection — MINOR
Problems: title "Failures became regression suites" — unnamed referent + "regression
suites" unglossed; "blind" undefined at first use; promotion rule is telegraphic
dash-prose.
Plan: name the subject in the title; pin "blind" in-line (agents don't know they're
tested; graded on traces not answers) or drop it; consider making the promotion rule
a short list. Keep the four dl rows.

### §3.10 Model tiering — CLEAR (skip)
Meets the bar (recently written). Optional: swap "The two suites split cleanly" for
"point to different winners" to kill the loose "split".

### §4 + JD appendix — MINOR
Problems: H2 "What this doesn't prove…" leads with the negative; repeated "corrected"
framing assumes a cold reader knows what was corrected from; appendix RAG cell packs
~8 claims into one run-on; "never learned whether its vectors were local or hosted"
mildly personifies code.
Plan: retitle H2 to name the subject (the limits); trim the "corrected" framing to
state what the eval does now; break the RAG appendix cell into 2–3 sentences;
"can't tell whether its vectors are local or hosted". Keep the four gap rows and the
honest pass-rate caveat.

---

## Round 2 — compression + clarity re-pass

Triggered by a read-through for redundant / non-additive language. Two problems
surfaced: the report summarizes itself across stacked layers (deck, hero
abstract, contents gist, section rail-gist, section lede) and repeats claims
across sections; and Round 1 left "plain words, still opaque" lines standing
(e.g. "intent is an annotation, not a control") because its bar was "no
metaphors, no obvious jargon," which is too low.

### Compression — done
- **Hero abstract (Objective/Design/Method) cut.** Deck + the three section
  rail-gists already carry it.
- **§1 opening** — folded the examples into the lede, dropped the job the
  rail-gist already states.
- **§1.1** — fixed the circular lede ("the target role *requires* each one, so
  they were built to demonstrate the skill") and stripped the repeated "because
  the role calls for it" from all three rows.
- **§2.1 quiet** — dropped the future-web-product story (kept in §4, its home);
  kept the outside-services fact.
- **§2.5 quiet** — cut the sentence re-listing the trace-contents dl above it.
- **§3.8 + §3.10 decision boxes** — cut the "deterministic work stays in the
  CLI" echoes; kept it where the cost argument is made (§2.1, §3.8 Cost).
- **§4 "Model routing" row** — was re-narrating §3.8+§3.10; now states the
  settled result + the one open gap.
- Net ≈485 words / 64 lines vs commit 3de7cb3.

### Compression — remaining
- Tighten content-bearing prose (not duplication — real judgment): the RRF
  justification (§2.4 Search dd), the mechanism paragraph (§3.7), the §3.8
  latency/cost write-ups.
- Decide the borderline repeat left in on purpose: the BM25 shared-vocabulary
  premise appears in §1.1 and again in §3.4. Kept both because §3.4 needs the
  premise to stand alone — confirm or collapse.

### Clarity re-pass — remaining (the main job)
New bar: **every line readable by someone who has never seen this project** —
not just "no metaphors, no jargon." Re-scan the whole doc for "plain words,
still opaque" lines and fix them. Known survivor already fixed: §2.4 intent
("The intent label doesn't change what the search returns…").

### Cleanup
- Delete the dead `.abstract` CSS (~30 lines) left after removing the abstract
  block. **Done.**

### The lesson (why passes keep missing things)
Two failure habits, both of which let bad lines survive:

1. **Scanning by term, not by reading cold.** Grepping for where a jargon noun
   first appears catches a late *word* but is blind to a presupposed *frame*
   made of plain words. "answers with cited passages from the book" (the deck)
   has no jargon token to grep, yet it assumes a Q&A setup the reader was never
   given. Read every sentence as a stranger who started at that sentence.
2. **Category exemptions.** "It's the deck / a preview / the audience knows it"
   is how presupposition survives — the block gets excused instead of tested.
   No line gets a pass for where it sits.

Presupposition pattern fixed this round: deck ("A founder brings it a business
question; it…"), §1 lede (dropped "any retrieval question" / "which one a turn
needs" before those exist), §1.1 namespace row (now introduces "namespace" and
"~200 passages" in plain terms instead of assuming them).
