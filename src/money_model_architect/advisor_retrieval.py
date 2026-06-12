"""Execute advisor queries against the local corpus index."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .advisor_queries import AdvisorQuery
from .retrieval import CorpusIndex
from .vector_store import layer_namespaces


RETRIEVAL_BACKENDS = ("bm25", "vector", "hybrid")
VECTOR_STORES = ("local", "pinecone")


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
    layers: list[str]
    target_namespaces: list[str]
    queried_namespaces: list[str | None]
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
    vector_store: str = "local",
    namespace_prefix: str = "money-models",
) -> list[QueryEvidence]:
    corpus_index = index or CorpusIndex.from_transcripts(transcript_dir)
    evidence: list[QueryEvidence] = []
    for query in queries:
        results = _search(
            corpus_index,
            query.query,
            layers=query.layers,
            top_k=top_k,
            retrieval_backend=retrieval_backend,
            vector_store=vector_store,
            namespace_prefix=namespace_prefix,
            target_namespaces=query.target_namespaces,
        )
        queried_namespaces = _physical_namespaces(
            query.target_namespaces,
            namespace_prefix=namespace_prefix,
        ) if retrieval_backend in {"vector", "hybrid"} else []
        evidence.append(
            QueryEvidence(
                intent=query.intent,
                layer=query.layer,
                layers=list(query.layers),
                target_namespaces=list(query.target_namespaces),
                queried_namespaces=list(queried_namespaces),
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
    layers: tuple[str, ...],
    top_k: int,
    retrieval_backend: str,
    vector_store: str = "local",
    namespace_prefix: str = "money-models",
    target_namespaces: tuple[str, ...] = (),
):
    if retrieval_backend == "bm25":
        return index.search(query, layers=layers, top_k=top_k)
    vector_namespaces = _physical_namespaces(target_namespaces, namespace_prefix=namespace_prefix)
    if retrieval_backend == "vector":
        return index.vector_search(
            query,
            layers=layers,
            top_k=top_k,
            vector_store_name=vector_store,
            vector_namespaces=vector_namespaces,
            namespace_prefix=namespace_prefix,
        )
    if retrieval_backend == "hybrid":
        return index.hybrid_search(
            query,
            layers=layers,
            top_k=top_k,
            vector_store_name=vector_store,
            vector_namespaces=vector_namespaces,
            namespace_prefix=namespace_prefix,
        )
    allowed = ", ".join(RETRIEVAL_BACKENDS)
    raise ValueError(f"unknown retrieval backend {retrieval_backend!r}; expected one of: {allowed}")


def _physical_namespaces(
    target_namespaces: tuple[str, ...],
    *,
    namespace_prefix: str,
) -> tuple[str | None, ...]:
    if not target_namespaces:
        return (None,)
    return tuple(layer_namespaces(target_namespaces, prefix=namespace_prefix))
