"""Execute advisor queries against the local corpus index."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .advisor_queries import AdvisorQuery
from .retrieval import CorpusIndex


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    chapter: str
    layer: str
    layers: list[str]
    score: float
    preview: str

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
) -> list[QueryEvidence]:
    corpus_index = index or CorpusIndex.from_transcripts(transcript_dir)
    evidence: list[QueryEvidence] = []
    for query in queries:
        results = corpus_index.search(query.query, layer=query.layer, top_k=top_k)
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
                    )
                    for result in results
                ],
            )
        )
    return evidence
