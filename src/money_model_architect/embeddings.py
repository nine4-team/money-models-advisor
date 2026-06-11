"""Embedding clients with a small disk cache."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence


class EmbeddingError(RuntimeError):
    """Raised when embeddings cannot be created."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def dot_product(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def vector_norm(vector: Sequence[float]) -> float:
    return sum(value * value for value in vector) ** 0.5


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    left_norm = vector_norm(left)
    right_norm = vector_norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot_product(left, right) / (left_norm * right_norm)


class OpenAIEmbeddingClient:
    """Minimal OpenAI embeddings client that caches by model and exact input text."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        cache_dir: Path | None = None,
        batch_size: int = 64,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        load_env_file(repo_root() / ".env")
        self.model = model or os.getenv("MMA_EMBEDDING_MODEL") or "text-embedding-3-small"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.cache_dir = cache_dir or repo_root() / ".cache" / "embeddings" / "openai" / self.model
        self.batch_size = batch_size
        self.base_url = base_url.rstrip("/")

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float] | None] = [None] * len(texts)
        misses: list[tuple[int, str, Path]] = []
        for index, text in enumerate(texts):
            cache_path = self._cache_path(text)
            cached = self._read_cache(cache_path)
            if cached is not None:
                embeddings[index] = cached
            else:
                misses.append((index, text, cache_path))

        if misses:
            if not self.api_key:
                raise EmbeddingError(
                    "OPENAI_API_KEY is required for uncached embeddings. "
                    "Set it in the environment or in the repo .env file."
                )
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            for start in range(0, len(misses), self.batch_size):
                batch = misses[start : start + self.batch_size]
                batch_embeddings = self._request_embeddings([text for _index, text, _path in batch])
                for (index, _text, cache_path), embedding in zip(batch, batch_embeddings, strict=True):
                    embeddings[index] = embedding
                    self._write_cache(cache_path, embedding)

        return [embedding for embedding in embeddings if embedding is not None]

    def _cache_path(self, text: str) -> Path:
        digest = hashlib.sha256(f"{self.model}\n{text}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path) -> list[float] | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not all(isinstance(value, int | float) for value in embedding):
            return None
        return [float(value) for value in embedding]

    def _write_cache(self, path: Path, embedding: Sequence[float]) -> None:
        path.write_text(
            json.dumps({"model": self.model, "embedding": list(embedding)}, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def _request_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        request = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=json.dumps({"model": self.model, "input": list(texts)}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise EmbeddingError(f"embedding request failed with HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise EmbeddingError(f"embedding request failed: {exc}") from exc

        data = payload.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise EmbeddingError("embedding response did not contain one vector per input")
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        embeddings = [item.get("embedding") for item in ordered]
        if not all(isinstance(embedding, list) for embedding in embeddings):
            raise EmbeddingError("embedding response contained an invalid vector")
        return [[float(value) for value in embedding] for embedding in embeddings]
