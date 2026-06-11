"""Vector storage adapters for local and hosted retrieval."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence

from .embeddings import cosine_similarity, load_env_file, repo_root


class VectorStoreError(RuntimeError):
    """Raised when a vector store cannot complete an operation."""


@dataclass(frozen=True)
class VectorRecord:
    id: str
    values: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorMatch:
    id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(Protocol):
    name: str

    def upsert(self, records: Sequence[VectorRecord], *, namespace: str | None = None) -> int:
        raise NotImplementedError

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        namespace: str | None = None,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        raise NotImplementedError


class LocalVectorStore:
    name = "local"

    def __init__(self, records: Sequence[VectorRecord] | None = None) -> None:
        self.records: dict[str, VectorRecord] = {}
        if records:
            self.upsert(records)

    def upsert(self, records: Sequence[VectorRecord], *, namespace: str | None = None) -> int:
        for record in records:
            self.records[record.id] = record
        return len(records)

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        namespace: str | None = None,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        matches: list[VectorMatch] = []
        for record in self.records.values():
            if not _metadata_matches(record.metadata, filter):
                continue
            score = cosine_similarity(vector, record.values)
            if score > 0:
                matches.append(VectorMatch(id=record.id, score=score, metadata=record.metadata))
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:top_k]


class PineconeVectorStore:
    name = "pinecone"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        index_host: str | None = None,
        namespace: str | None = None,
    ) -> None:
        load_env_file(repo_root() / ".env")
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_host = (index_host or os.getenv("PINECONE_INDEX_HOST") or "").rstrip("/")
        self.default_namespace = namespace or os.getenv("MMA_PINECONE_NAMESPACE") or "money-models"
        if self.index_host and not self.index_host.startswith(("http://", "https://")):
            self.index_host = f"https://{self.index_host}"

    @classmethod
    def from_env(cls) -> "PineconeVectorStore":
        return cls()

    def upsert(self, records: Sequence[VectorRecord], *, namespace: str | None = None) -> int:
        self._require_config()
        if not records:
            return 0
        payload = {
            "vectors": [
                {
                    "id": record.id,
                    "values": record.values,
                    "metadata": record.metadata,
                }
                for record in records
            ],
            "namespace": namespace or self.default_namespace,
        }
        self._request("POST", "/vectors/upsert", payload)
        return len(records)

    def query(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        namespace: str | None = None,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        self._require_config()
        payload: dict[str, Any] = {
            "vector": list(vector),
            "topK": top_k,
            "includeMetadata": True,
            "namespace": namespace or self.default_namespace,
        }
        if filter:
            payload["filter"] = filter
        response = self._request("POST", "/query", payload)
        matches = response.get("matches", [])
        if not isinstance(matches, list):
            raise VectorStoreError("Pinecone query response did not contain matches")
        return [
            VectorMatch(
                id=str(match.get("id", "")),
                score=float(match.get("score", 0.0)),
                metadata=match.get("metadata", {}) if isinstance(match.get("metadata"), dict) else {},
            )
            for match in matches
        ]

    def _require_config(self) -> None:
        if not self.api_key:
            raise VectorStoreError("PINECONE_API_KEY is required for Pinecone vector store operations")
        if not self.index_host:
            raise VectorStoreError("PINECONE_INDEX_HOST is required for Pinecone vector store operations")

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.index_host}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Api-Key": self.api_key or "",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VectorStoreError(f"Pinecone request failed with HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise VectorStoreError(f"Pinecone request failed: {exc}") from exc
        return json.loads(body) if body.strip() else {}


def selected_vector_store_name(name: str | None = None) -> str:
    return (name or os.getenv("MMA_VECTOR_STORE") or "local").strip().lower()


def vector_id(*, chunking_strategy: str, embedding_model: str, chunk_id: str) -> str:
    safe_model = embedding_model.replace("/", "_")
    return f"{chunking_strategy}:{safe_model}:{chunk_id}"


def chunk_id_from_vector_id(vector_id_value: str) -> str:
    parts = vector_id_value.split(":", 2)
    return parts[2] if len(parts) == 3 else vector_id_value


def _metadata_matches(metadata: dict[str, Any], filter: dict[str, Any] | None) -> bool:
    if not filter:
        return True
    for key, expected in filter.items():
        actual = metadata.get(key)
        if isinstance(expected, dict) and "$in" in expected:
            options = expected["$in"]
            if isinstance(actual, list):
                if not any(item in options for item in actual):
                    return False
            elif actual not in options:
                return False
        elif actual != expected:
            return False
    return True
