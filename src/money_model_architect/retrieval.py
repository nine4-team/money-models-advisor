"""Small local retrieval engine over the transcript corpus.

This is not a replacement for the planned hybrid Pinecone/BM25/rerank stack.
It is the runnable proof that the namespace taxonomy, chunk provenance, and
retrieval evals can exist before external services are introduced.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .namespaces import route_for_chapter

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
HEADING_RE = re.compile(r"(?=## \[§[^]]+\])")
FRAMEWORK_BOUNDARY_RE = re.compile(
    r"(?=(?:\n\n|\. )(?:(?:So )?(?:how (?:it|this) works|how to use|how I learned|description|examples?|important points?|summary|"
    r"the objective|the key|the rule|here(?:'s| is| are)|step (?:one|two|three|four|five|1|2|3|4|5)|"
    r"first[, ]|second[, ]|third[, ]|finally[, ])))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ChunkingStrategy:
    name: str
    mode: str
    target_words: int = 450
    overlap_words: int = 70


CHUNKING_STRATEGIES: dict[str, ChunkingStrategy] = {
    "fixed-300": ChunkingStrategy("fixed-300", "fixed", target_words=300, overlap_words=50),
    "fixed-512": ChunkingStrategy("fixed-512", "fixed", target_words=512, overlap_words=80),
    "fixed-800": ChunkingStrategy("fixed-800", "fixed", target_words=800, overlap_words=120),
    "heading-aware": ChunkingStrategy("heading-aware", "heading", target_words=450, overlap_words=70),
    "framework-aware": ChunkingStrategy("framework-aware", "framework", target_words=650, overlap_words=90),
}


@dataclass(frozen=True)
class Chunk:
    id: str
    chapter: str
    layer: str
    layers: tuple[str, ...]
    text: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _split_fixed(text: str, target_words: int, overlap_words: int) -> list[tuple[str, int, int]]:
    words = text.split()
    chunks: list[tuple[str, int, int]] = []
    step = max(1, target_words - overlap_words)
    cursor = 0
    for start_word in range(0, len(words), step):
        window = words[start_word : start_word + target_words]
        if not window:
            continue
        chunk_text = " ".join(window)
        char_start = text.find(window[0], cursor)
        if char_start < 0:
            char_start = 0
        char_end = char_start + len(chunk_text)
        chunks.append((chunk_text, max(0, char_start), min(len(text), char_end)))
        cursor = max(cursor, char_start)
        if start_word + target_words >= len(words):
            break
    return chunks


def split_text(text: str, strategy: ChunkingStrategy) -> list[tuple[str, int, int]]:
    if strategy.mode == "fixed":
        return _split_fixed(text, strategy.target_words, strategy.overlap_words)

    parts = [part.strip() for part in HEADING_RE.split(text) if part.strip()]
    if len(parts) == 1:
        if strategy.mode == "framework":
            framework_parts = _split_framework_boundaries(text)
            if len(framework_parts) > 1:
                return _limit_long_parts(text, framework_parts, strategy)
        return _split_fixed(text, strategy.target_words, strategy.overlap_words)

    chunks = []
    cursor = 0
    for part in parts:
        char_start = text.find(part, cursor)
        char_end = char_start + len(part)
        if strategy.mode == "framework":
            for sub_text, sub_start, sub_end in _limit_long_parts(text, [(part, char_start, char_end)], strategy):
                chunks.append((sub_text, sub_start, sub_end))
        else:
            chunks.append((part, char_start, char_end))
        cursor = char_end
    return chunks


def _split_framework_boundaries(text: str) -> list[tuple[str, int, int]]:
    matches = [match.start() for match in FRAMEWORK_BOUNDARY_RE.finditer(text)]
    starts = [0]
    for match_start in matches:
        if match_start - starts[-1] > 350:
            starts.append(match_start)
    starts.append(len(text))

    parts = []
    for start, end in zip(starts, starts[1:]):
        part = text[start:end].strip()
        if not part:
            continue
        char_start = text.find(part, start)
        parts.append((part, char_start, char_start + len(part)))
    return parts


def _limit_long_parts(
    source_text: str,
    parts: list[tuple[str, int, int]],
    strategy: ChunkingStrategy,
) -> list[tuple[str, int, int]]:
    limited = []
    for part, char_start, _char_end in parts:
        word_count = len(tokenize(part))
        if word_count <= strategy.target_words * 1.3:
            limited.append((part, char_start, char_start + len(part)))
            continue

        fixed_parts = _split_fixed(part, strategy.target_words, strategy.overlap_words)
        for fixed_text, fixed_start, fixed_end in fixed_parts:
            global_start = source_text.find(fixed_text.split()[0], char_start + fixed_start) if fixed_text.split() else char_start
            if global_start < 0:
                global_start = char_start + fixed_start
            limited.append((fixed_text, global_start, global_start + len(fixed_text[: fixed_end - fixed_start])))
    return limited


class CorpusIndex:
    def __init__(self, chunks: list[Chunk], strategy: ChunkingStrategy = CHUNKING_STRATEGIES["heading-aware"]):
        self.chunks = chunks
        self.strategy = strategy
        self._term_freqs = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self._doc_freqs: dict[str, int] = defaultdict(int)
        for terms in self._term_freqs:
            for term in terms:
                self._doc_freqs[term] += 1
        self._avg_len = sum(sum(terms.values()) for terms in self._term_freqs) / max(1, len(self._term_freqs))

    @classmethod
    def from_transcripts(cls, transcript_dir: Path, chunking: str | ChunkingStrategy = "heading-aware") -> "CorpusIndex":
        strategy = resolve_chunking_strategy(chunking)
        chunks: list[Chunk] = []
        for path in sorted(transcript_dir.glob("*.txt")):
            chapter = path.stem
            route = route_for_chapter(chapter)
            text = path.read_text(encoding="utf-8")
            for index, (chunk_text, char_start, char_end) in enumerate(split_text(text, strategy)):
                chunks.append(
                    Chunk(
                        id=f"{chapter}:{index}",
                        chapter=chapter,
                        layer=route.primary_layer,
                        layers=route.layers,
                        text=chunk_text,
                        char_start=char_start,
                        char_end=char_end,
                    )
                )
        return cls(chunks, strategy=strategy)

    def average_chunk_words(self) -> float:
        if not self.chunks:
            return 0.0
        return sum(len(tokenize(chunk.text)) for chunk in self.chunks) / len(self.chunks)

    def search(self, query: str, layer: str | None = None, top_k: int = 5) -> list[SearchResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        results: list[SearchResult] = []
        query_counts = Counter(query_terms)
        for chunk, terms in zip(self.chunks, self._term_freqs, strict=True):
            if layer and layer not in chunk.layers:
                continue
            score = self._bm25(query_counts, terms)
            if score > 0:
                results.append(SearchResult(chunk=chunk, score=score))
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

    def _bm25(self, query_counts: Counter[str], terms: Counter[str]) -> float:
        k1 = 1.5
        b = 0.75
        doc_len = sum(terms.values())
        score = 0.0
        total_docs = max(1, len(self.chunks))
        for term, query_weight in query_counts.items():
            tf = terms.get(term, 0)
            if not tf:
                continue
            df = self._doc_freqs.get(term, 0)
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * doc_len / max(1.0, self._avg_len))
            score += query_weight * idf * (tf * (k1 + 1)) / denom
        return score


def resolve_chunking_strategy(chunking: str | ChunkingStrategy) -> ChunkingStrategy:
    if isinstance(chunking, ChunkingStrategy):
        return chunking
    try:
        return CHUNKING_STRATEGIES[chunking]
    except KeyError as exc:
        allowed = ", ".join(sorted(CHUNKING_STRATEGIES))
        raise ValueError(f"unknown chunking strategy {chunking!r}; expected one of: {allowed}") from exc
