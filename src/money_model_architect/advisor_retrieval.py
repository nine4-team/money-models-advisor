"""Execute advisor queries against the local corpus index."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .advisor_queries import AdvisorQuery
from .retrieval import CorpusIndex


RETRIEVAL_BACKENDS = ("bm25", "vector", "hybrid")


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    chapter: str
    layer: str
    layers: list[str]
    score: float
    preview: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class QueryEvidence:
    intent: str
    layer: str | None
    query: str
    reason: str
    chunks: list[EvidenceChunk]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["chunks"] = [chunk.to_dict() for chunk in self.chunks]
        return payload


def execute_advisor_queries(
    queries: list[AdvisorQuery],
    transcript_dir: Path,
    top_k: int = 3,
    index: CorpusIndex | None = None,
    retrieval_backend: str = "bm25",
) -> list[QueryEvidence]:
    corpus_index = index or CorpusIndex.from_transcripts(transcript_dir)
    evidence: list[QueryEvidence] = []
    for query in queries:
        results = _search(corpus_index, query.query, layer=query.layer, top_k=top_k, retrieval_backend=retrieval_backend)
        evidence.append(
            QueryEvidence(
                intent=query.intent,
                layer=query.layer,
                query=query.query,
                reason=query.reason,
                chunks=[
                    EvidenceChunk(
                        id=result.chunk.id,
                        chapter=result.chunk.chapter,
                        layer=result.chunk.layer,
                        layers=list(result.chunk.layers),
                        score=round(result.score, 3),
                        preview=result.chunk.text[:360].replace("\n", " "),
                        text=result.chunk.text,
                    )
                    for result in results
                ],
            )
        )
    return evidence


def _search(
    index: CorpusIndex,
    query: str,
    *,
    layer: str | None,
    top_k: int,
    retrieval_backend: str,
):
    if retrieval_backend == "bm25":
        return index.search(query, layer=layer, top_k=top_k)
    if retrieval_backend == "vector":
        return index.vector_search(query, layer=layer, top_k=top_k)
    if retrieval_backend == "hybrid":
        return index.hybrid_search(query, layer=layer, top_k=top_k)
    allowed = ", ".join(RETRIEVAL_BACKENDS)
    raise ValueError(f"unknown retrieval backend {retrieval_backend!r}; expected one of: {allowed}")
