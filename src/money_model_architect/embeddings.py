"""OpenAI embedding client with a small SQLite cache."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"


@dataclass(frozen=True)
class EmbeddingUsage:
    prompt_tokens: int = 0
    total_tokens: int = 0
    api_requests: int = 0
    cache_hits: int = 0


class EmbeddingCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                cache_key TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                dimensions INTEGER,
                text_sha256 TEXT NOT NULL,
                embedding_json TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def get(self, model: str, dimensions: int | None, text: str) -> list[float] | None:
        key = cache_key(model, dimensions, text)
        row = self.conn.execute("SELECT embedding_json FROM embeddings WHERE cache_key = ?", (key,)).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, model: str, dimensions: int | None, text: str, embedding: list[float]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO embeddings (cache_key, model, dimensions, text_sha256, embedding_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cache_key(model, dimensions, text),
                model,
                dimensions,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                json.dumps(embedding, separators=(",", ":")),
            ),
        )
        self.conn.commit()


class OpenAIEmbeddingClient:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
        cache_path: Path | None = None,
        api_key: str | None = None,
    ):
        self.model = model
        self.dimensions = dimensions
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.cache = EmbeddingCache(cache_path or Path(".cache/embeddings.sqlite3"))

    def embed_many(self, texts: list[str], batch_size: int = 64) -> tuple[list[list[float]], EmbeddingUsage]:
        vectors: list[list[float] | None] = []
        missing: list[tuple[int, str]] = []
        cache_hits = 0

        for index, text in enumerate(texts):
            cached = self.cache.get(self.model, self.dimensions, text)
            if cached is None:
                vectors.append(None)
                missing.append((index, text))
            else:
                vectors.append(cached)
                cache_hits += 1

        usage = EmbeddingUsage(cache_hits=cache_hits)
        if missing:
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY is required for uncached OpenAI embeddings")
            for start in range(0, len(missing), batch_size):
                batch = missing[start : start + batch_size]
                embedded, batch_usage = self._embed_uncached([text for _index, text in batch])
                usage = EmbeddingUsage(
                    prompt_tokens=usage.prompt_tokens + batch_usage.prompt_tokens,
                    total_tokens=usage.total_tokens + batch_usage.total_tokens,
                    api_requests=usage.api_requests + 1,
                    cache_hits=usage.cache_hits,
                )
                for (original_index, text), vector in zip(batch, embedded, strict=True):
                    self.cache.set(self.model, self.dimensions, text, vector)
                    vectors[original_index] = vector

        return [vector for vector in vectors if vector is not None], usage

    def _embed_uncached(self, texts: list[str]) -> tuple[list[list[float]], EmbeddingUsage]:
        body: dict[str, object] = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }
        if self.dimensions is not None:
            body["dimensions"] = self.dimensions
        request = urllib.request.Request(
            OPENAI_EMBEDDINGS_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI embeddings request failed: {exc.code} {detail}") from exc

        data = sorted(payload["data"], key=lambda item: item["index"])
        usage = payload.get("usage", {})
        return [item["embedding"] for item in data], EmbeddingUsage(
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        )


def cache_key(model: str, dimensions: int | None, text: str) -> str:
    raw = json.dumps(
        {
            "model": model,
            "dimensions": dimensions,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for left, right in zip(a, b, strict=True):
        dot += left * right
        norm_a += left * left
        norm_b += right * right
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / ((norm_a**0.5) * (norm_b**0.5))

