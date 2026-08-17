# Corpus

Read-only source material for retrieval experiments. Do not edit derived source text
in place; re-import it from the authorized upstream source.

| Path | Contents | Current role |
|---|---|---|
| `transcripts/` | 32 chapter transcripts from *$100M Money Models* | Primary corpus for chunking and retrieval |
| `money-models-frameworks.md` | Hand-distilled framework summary | Input to the versioned query-generation corpus guide |
| `coach/` | Earlier coaching and decision-tree artifacts | Historical design reference, not executable runtime policy |
| `skill/` | Earlier skill/config artifacts | Historical tool-boundary reference |

## Current ingestion path

The framework-aware chunker reads the transcripts, preserves chapter and subject
metadata, and produces the records used by both local and Pinecone retrieval. The
selected hosted layout stores those records in one unfiltered namespace. The subject
taxonomy remains metadata and supports controlled experiments; it is not a
request-time filter in the active advisor path.

The active agent writes one corpus-guided query from the current user question,
normal saved business context, and `evals/query_generation/corpus_guide_v1.json`.
Hybrid retrieval executes that query over the framework-aware chunks.

## Provenance and redistribution

The materials were imported from private shared resources used during development.
They remain subject to their original rights and are not covered by this repository's
MIT license. See `../DATA_AND_CONTENT_NOTICE.md` before redistributing the repository.
