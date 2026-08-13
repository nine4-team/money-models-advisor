#!/usr/bin/env python3
"""Revalidate connected retrieval choices on the active 46-case query path.

Chunking and Pinecone checks hold the winning gpt-5.5 query fixed. The matrix
command replays every frozen query approach and writer through both retrievers.
No model generation occurs in this script.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.embeddings import OpenAIEmbeddingClient  # noqa: E402
from money_model_architect.namespaces import route_for_chapter  # noqa: E402
from money_model_architect.retrieval import CHUNKING_STRATEGIES, Chunk, CorpusIndex, tokenize  # noqa: E402
from money_model_architect.vector_store import (  # noqa: E402
    LocalVectorStore,
    PineconeVectorStore,
    subject_namespaces,
)


BASE_CASES = ROOT / "evals" / "advisor_search_query_cases_enriched_labels.jsonl"
EXPANSION_CASES = ROOT / "evals" / "query_generation" / "query_generation_holdout_v1.jsonl"
DEV_RUNS = ROOT / "evals" / "runs" / "query_generation" / "v2"
EXPANSION_RUNS = ROOT / "evals" / "runs" / "query_generation" / "holdout_v1"
REPORT_DIR = ROOT / "evals" / "reports"
DEFAULT_ADJUDICATIONS = ROOT / "evals" / "active_query_chunking_adjudications.jsonl"
DEFAULT_EMBEDDING_ADJUDICATIONS = ROOT / "evals" / "embedding_model_adjudications.jsonl"
MODEL = "gpt-5.5"
METHOD = "guided_model_rewrite_v2"
CONTROL_EMBEDDING_MODEL = "text-embedding-3-small"
ACTIVE_PINECONE_NAMESPACE = "money-models-framework-large-d1536"

MATRIX_CONDITIONS = (
    ("raw_question", None),
    ("model_rewrite", "gpt-5.5"),
    ("model_rewrite", "gpt-5.4-mini"),
    ("guided_model_rewrite_v2", "gpt-5.5"),
    ("guided_model_rewrite_v2", "gpt-5.4-mini"),
)


@dataclass(frozen=True)
class Case:
    case_id: str
    user_turn: str
    query: str
    known_useful_chunk_ids: tuple[str, ...]
    oracle_subjects: tuple[str, ...]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def generation_path(case_id: str) -> Path:
    runs = EXPANSION_RUNS if case_id.startswith("querygen_holdout") else DEV_RUNS
    return runs / MODEL / METHOD / case_id / "generation.json"


def subjects_from_labels(chunk_ids: Iterable[str]) -> tuple[str, ...]:
    subjects: list[str] = []
    for chunk_id in chunk_ids:
        chapter = chunk_id.split(":", 1)[0]
        for subject in route_for_chapter(chapter).subjects:
            if subject not in subjects:
                subjects.append(subject)
    return tuple(subjects)


def load_cases() -> list[Case]:
    rows = [*load_jsonl(BASE_CASES), *load_jsonl(EXPANSION_CASES)]
    cases: list[Case] = []
    for row in rows:
        path = generation_path(row["case_id"])
        generation = json.loads(path.read_text(encoding="utf-8"))
        useful = tuple(row["known_useful_chunk_ids"])
        expected = tuple(row.get("expected_subjects", ()))
        cases.append(
            Case(
                case_id=row["case_id"],
                user_turn=row["user_turn"],
                query=generation["query"],
                known_useful_chunk_ids=useful,
                oracle_subjects=expected or subjects_from_labels(useful),
            )
        )
    if len(cases) != 46:
        raise ValueError(f"expected 46 cases, found {len(cases)}")
    return cases


def matrix_generation_path(case_id: str, method: str, model: str | None) -> Path:
    if case_id.startswith("querygen_holdout"):
        runs = EXPANSION_RUNS
    elif method in {"raw_question", "model_rewrite"} and model in {None, "gpt-5.5"}:
        runs = ROOT / "evals" / "runs" / "query_generation" / "v1"
    else:
        runs = DEV_RUNS
    model_dir = model or "gpt-5.5"
    return runs / model_dir / method / case_id / "generation.json"


def load_matrix_cases() -> list[dict[str, Any]]:
    rows = [*load_jsonl(BASE_CASES), *load_jsonl(EXPANSION_CASES)]
    matrix_cases: list[dict[str, Any]] = []
    for row in rows:
        queries: dict[str, str] = {}
        for method, model in MATRIX_CONDITIONS:
            path = matrix_generation_path(row["case_id"], method, model)
            generation = json.loads(path.read_text(encoding="utf-8"))
            if not generation.get("valid"):
                raise ValueError(f"invalid frozen generation: {path}")
            key = f"{method}:{model or 'none'}"
            queries[key] = generation["query"]
        matrix_cases.append({**row, "queries": queries})
    if len(matrix_cases) != 46:
        raise ValueError(f"expected 46 matrix cases, found {len(matrix_cases)}")
    return matrix_cases


def load_adjudications(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    rows = load_jsonl(path)
    return {
        (row["strategy"], row["case_id"], row["chunk_id"]): row
        for row in rows
    }


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _find_token_span(source: list[str], needle: list[str], estimated_start: int) -> tuple[int, int]:
    if not needle:
        raise ValueError("cannot locate an empty chunk")
    candidates: list[int] = []
    first = needle[0]
    last_start = len(source) - len(needle)
    for start in range(max(0, last_start + 1)):
        if source[start] == first and source[start : start + len(needle)] == needle:
            candidates.append(start)
    if not candidates:
        raise ValueError(f"could not locate {len(needle)}-token chunk in transcript")
    start = min(candidates, key=lambda value: abs(value - estimated_start))
    return start, start + len(needle)


def chunk_token_spans(index: CorpusIndex) -> dict[str, tuple[int, int]]:
    transcript_dir = ROOT / "corpus" / "transcripts"
    sources = {
        path.stem: (path.read_text(encoding="utf-8"), tokenize(path.read_text(encoding="utf-8")))
        for path in transcript_dir.glob("*.txt")
    }
    spans: dict[str, tuple[int, int]] = {}
    for chunk in index.chunks:
        source_text, source_tokens = sources[chunk.chapter]
        estimated = round(chunk.char_start / max(1, len(source_text)) * len(source_tokens))
        spans[chunk.id] = _find_token_span(source_tokens, tokenize(chunk.text), estimated)
    return spans


def transferred_label(
    candidate: Chunk,
    useful_chunks: list[Chunk],
    *,
    candidate_span: tuple[int, int],
    heading_spans: dict[str, tuple[int, int]],
    exact_heading_ids: set[str],
    strategy: str,
) -> tuple[bool, list[dict[str, Any]]]:
    if strategy == "heading-aware":
        return candidate.id in exact_heading_ids, (
            [{"heading_chunk_id": candidate.id, "exact_id_match": True}]
            if candidate.id in exact_heading_ids
            else []
        )
    matches: list[dict[str, Any]] = []
    candidate_len = max(1, candidate_span[1] - candidate_span[0])
    for useful in useful_chunks:
        if candidate.chapter != useful.chapter:
            continue
        useful_span = heading_spans[useful.id]
        overlap = max(0, min(candidate_span[1], useful_span[1]) - max(candidate_span[0], useful_span[0]))
        if not overlap:
            continue
        useful_len = max(1, useful_span[1] - useful_span[0])
        coverage = overlap / min(candidate_len, useful_len)
        matches.append(
            {
                "heading_chunk_id": useful.id,
                "overlap_tokens": overlap,
                "overlap_of_shorter": round(coverage, 4),
            }
        )
    # Boundary-only overlap should not transfer a usefulness label. Requiring
    # 20 tokens and 15% of the shorter span preserves substantive source
    # content while accommodating both small framework splits and large windows.
    useful = any(
        match["overlap_tokens"] >= 20 and match["overlap_of_shorter"] >= 0.15
        for match in matches
    )
    return useful, matches


def summarize(rows: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    first_ranks = [row["first_useful_rank"] for row in rows if row["first_useful_rank"] is not None]
    useful_results = sum(row["useful_result_count"] for row in rows)
    slots = len(rows) * top_k
    precision = 100 * useful_results / slots
    latencies = [row["latency_ms"] for row in rows]
    returned_words = [row.get("returned_word_count", 0) for row in rows]
    return {
        "cases": len(rows),
        "hit_at_1_pct": round(100 * sum(rank == 1 for rank in first_ranks) / len(rows), 1),
        "hit_at_3_pct": round(100 * sum(rank <= 3 for rank in first_ranks) / len(rows), 1),
        "hit_at_5_pct": round(100 * len(first_ranks) / len(rows), 1),
        "mean_first_useful_rank": round(statistics.mean(first_ranks), 3) if first_ranks else None,
        "useful_at_5_pct": round(precision, 1),
        "noise_at_5_pct": round(100 - precision, 1),
        "mean_returned_words": round(statistics.mean(returned_words), 1),
        "p50_returned_words": round(statistics.median(returned_words), 1),
        "mean_latency_ms": round(statistics.mean(latencies), 2),
        "p50_latency_ms": round(statistics.median(latencies), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "misses": [row["case_id"] for row in rows if row["first_useful_rank"] is None],
    }


def build_local_store(index: CorpusIndex, client: OpenAIEmbeddingClient) -> LocalVectorStore:
    return LocalVectorStore(index.vector_records(client))


def control_embedding_client() -> OpenAIEmbeddingClient:
    """Return the embedding setup held constant in the historical control matrix."""
    return OpenAIEmbeddingClient(model=CONTROL_EMBEDDING_MODEL)


def run_chunking(args: argparse.Namespace) -> int:
    cases = load_cases()
    adjudications = load_adjudications(args.adjudications)
    client = control_embedding_client()
    heading_index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    heading_by_id = {chunk.id: chunk for chunk in heading_index.chunks}
    heading_spans = chunk_token_spans(heading_index)
    all_rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}

    for strategy in args.strategies:
        print(f"building {strategy}", file=sys.stderr)
        index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=strategy)
        chunk_words = [len(tokenize(chunk.text)) for chunk in index.chunks]
        strategy_spans = chunk_token_spans(index)
        store = build_local_store(index, client)
        strategy_rows: list[dict[str, Any]] = []
        for case in cases:
            useful_heading = [heading_by_id[chunk_id] for chunk_id in case.known_useful_chunk_ids if chunk_id in heading_by_id]
            exact_heading_ids = set(case.known_useful_chunk_ids)
            started = time.perf_counter()
            results = index.hybrid_search(
                case.query,
                top_k=args.top_k,
                embedding_client=client,
                vector_store=store,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            candidates = []
            first_rank = None
            useful_count = 0
            returned_word_count = 0
            for rank, result in enumerate(results, start=1):
                useful, matches = transferred_label(
                    result.chunk,
                    useful_heading,
                    candidate_span=strategy_spans[result.chunk.id],
                    heading_spans=heading_spans,
                    exact_heading_ids=exact_heading_ids,
                    strategy=strategy,
                )
                transferred_useful = useful
                adjudication = adjudications.get((strategy, case.case_id, result.chunk.id))
                if adjudication is not None:
                    useful = bool(adjudication["useful"])
                if useful:
                    useful_count += 1
                    first_rank = first_rank or rank
                word_count = len(tokenize(result.chunk.text))
                returned_word_count += word_count
                candidates.append(
                    {
                        "rank": rank,
                        "strategy_chunk_id": f"{strategy}:{result.chunk.id}",
                        "chunk_id": result.chunk.id,
                        "chapter": result.chunk.chapter,
                        "char_start": result.chunk.char_start,
                        "char_end": result.chunk.char_end,
                        "score": round(result.score, 8),
                        "word_count": word_count,
                        "useful": useful,
                        "transferred_useful": transferred_useful,
                        "label_source": "semantic_adjudication" if adjudication else "span_transfer",
                        "adjudication_rationale": adjudication.get("rationale") if adjudication else None,
                        "transfer_matches": matches,
                        "text": result.chunk.text,
                    }
                )
            row = {
                "case_id": case.case_id,
                "user_turn": case.user_turn,
                "query": case.query,
                "strategy": strategy,
                "first_useful_rank": first_rank,
                "useful_result_count": useful_count,
                "returned_word_count": returned_word_count,
                "latency_ms": round(latency_ms, 3),
                "candidates": candidates,
            }
            strategy_rows.append(row)
            all_rows.append(row)
        summaries[strategy] = {
            "chunks": len(index.chunks),
            "avg_chunk_words": round(index.average_chunk_words(), 1),
            "p95_chunk_words": round(percentile(chunk_words, 95), 1),
            "max_chunk_words": max(chunk_words),
            "chunks_over_1000_words": sum(words > 1000 for words in chunk_words),
            **summarize(strategy_rows, top_k=args.top_k),
        }

    summary = {
        "experiment": "active-query-chunking-revalidation",
        "cases": len(cases),
        "query_writer": f"{MODEL}/{METHOD}",
        "embedding_model": client.embedding_id,
        "retriever": "local hybrid, unfiltered",
        "label_transfer": "source-span overlap with audited heading-aware useful chunks",
        "semantic_adjudications": len(adjudications),
        "strategies": summaries,
    }
    write_json(args.summary, summary)
    write_jsonl(args.cases_output, all_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def run_matrix(args: argparse.Namespace) -> int:
    cases = load_matrix_cases()
    adjudications = load_adjudications(args.adjudications)
    client = control_embedding_client()
    heading_index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    heading_by_id = {chunk.id: chunk for chunk in heading_index.chunks}
    heading_spans = chunk_token_spans(heading_index)
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)
    strategy_spans = chunk_token_spans(index)
    store = build_local_store(index, client)
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for method, model in MATRIX_CONDITIONS:
        condition_key = f"{method}:{model or 'none'}"
        for backend in ("bm25", "hybrid"):
            print(f"running {condition_key} {backend}", file=sys.stderr)
            condition_rows: list[dict[str, Any]] = []
            for case in cases:
                query = case["queries"][condition_key]
                started = time.perf_counter()
                if backend == "bm25":
                    results = index.search(query, top_k=args.top_k)
                else:
                    results = index.hybrid_search(
                        query,
                        top_k=args.top_k,
                        embedding_client=client,
                        vector_store=store,
                    )
                latency_ms = (time.perf_counter() - started) * 1000
                useful_heading = [
                    heading_by_id[chunk_id]
                    for chunk_id in case["known_useful_chunk_ids"]
                    if chunk_id in heading_by_id
                ]
                candidates = []
                useful_ids: list[str] = []
                first_rank = None
                returned_word_count = 0
                for rank, result in enumerate(results, start=1):
                    transferred_useful, matches = transferred_label(
                        result.chunk,
                        useful_heading,
                        candidate_span=strategy_spans[result.chunk.id],
                        heading_spans=heading_spans,
                        exact_heading_ids=set(case["known_useful_chunk_ids"]),
                        strategy=args.chunking,
                    )
                    adjudication = adjudications.get((args.chunking, case["case_id"], result.chunk.id))
                    useful = bool(adjudication["useful"]) if adjudication else transferred_useful
                    if useful:
                        useful_ids.append(result.chunk.id)
                        first_rank = first_rank or rank
                    word_count = len(tokenize(result.chunk.text))
                    returned_word_count += word_count
                    candidates.append(
                        {
                            "rank": rank,
                            "chunk_id": result.chunk.id,
                            "chapter": result.chunk.chapter,
                            "char_start": result.chunk.char_start,
                            "char_end": result.chunk.char_end,
                            "score": round(result.score, 8),
                            "word_count": word_count,
                            "useful": useful,
                            "transferred_useful": transferred_useful,
                            "label_source": "semantic_adjudication" if adjudication else "span_transfer",
                            "adjudication_rationale": adjudication.get("rationale") if adjudication else None,
                            "transfer_matches": matches,
                            "text": result.chunk.text,
                        }
                    )
                row = {
                    "approach": method,
                    "model": model,
                    "retriever": backend,
                    "chunking": args.chunking,
                    "case_id": case["case_id"],
                    "user_turn": case["user_turn"],
                    "query": query,
                    "first_useful_rank": first_rank,
                    "useful_result_count": len(useful_ids),
                    "useful_returned_chunk_ids": useful_ids,
                    "returned_word_count": returned_word_count,
                    "latency_ms": round(latency_ms, 3),
                    "candidates": candidates,
                }
                condition_rows.append(row)
                all_rows.append(row)
            summaries.append(
                {
                    "approach": method,
                    "model": model,
                    "retriever": backend,
                    **summarize(condition_rows, top_k=args.top_k),
                }
            )

    summary = {
        "experiment": "active-framework-query-model-retriever-matrix",
        "cases": len(cases),
        "chunking": args.chunking,
        "top_k": args.top_k,
        "query_policy": "frozen saved queries; no regeneration",
        "retrieval_policy": "local, unfiltered",
        "embedding_model": client.embedding_id,
        "label_transfer": "source-span overlap with audited heading-aware useful chunks plus semantic adjudications",
        "semantic_adjudications": sum(
            strategy == args.chunking
            for strategy, _case_id, _chunk_id in adjudications
        ),
        "results": summaries,
    }
    write_json(args.summary, summary)
    write_jsonl(args.cases_output, all_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def pinecone_case(
    case: Case,
    *,
    index: CorpusIndex,
    client: OpenAIEmbeddingClient,
    store: PineconeVectorStore,
    namespaces: tuple[str | None, ...] | None,
    policy: str,
    top_k: int,
    namespace_prefix: str,
    strategy_spans: dict[str, tuple[int, int]],
    heading_spans: dict[str, tuple[int, int]],
    heading_by_id: dict[str, Chunk],
    strategy: str,
    adjudications: dict[tuple[str, str, str], dict[str, Any]],
    embedding_adjudications: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    started = time.perf_counter()
    results = index.hybrid_search(
        case.query,
        top_k=top_k,
        embedding_client=client,
        vector_store=store,
        vector_namespaces=namespaces,
        namespace_prefix=namespace_prefix,
    )
    latency_ms = (time.perf_counter() - started) * 1000
    returned = [result.chunk.id for result in results]
    returned_word_count = sum(len(tokenize(result.chunk.text)) for result in results)
    useful_heading = [heading_by_id[chunk_id] for chunk_id in case.known_useful_chunk_ids if chunk_id in heading_by_id]
    useful_flags = [
        bool(embedding_adjudications[(case.case_id, result.chunk.id)]["useful"])
        if (case.case_id, result.chunk.id) in embedding_adjudications
        else bool(adjudications[(strategy, case.case_id, result.chunk.id)]["useful"])
        if (strategy, case.case_id, result.chunk.id) in adjudications
        else transferred_label(
                result.chunk,
                useful_heading,
                candidate_span=strategy_spans[result.chunk.id],
                heading_spans=heading_spans,
                exact_heading_ids=set(case.known_useful_chunk_ids),
                strategy=strategy,
            )[0]
        for result in results
    ]
    ranks = [rank for rank, useful in enumerate(useful_flags, start=1) if useful]
    useful_ids = [chunk_id for chunk_id, useful in zip(returned, useful_flags, strict=True) if useful]
    return {
        "case_id": case.case_id,
        "policy": policy,
        "query": case.query,
        "namespaces": list(namespaces or (store.default_namespace,)),
        "returned_chunk_ids": returned,
        "first_useful_rank": min(ranks) if ranks else None,
        "useful_result_count": len(useful_ids),
        "returned_word_count": returned_word_count,
        "useful_returned_chunk_ids": useful_ids,
        "latency_ms": round(latency_ms, 3),
    }


def run_pinecone(args: argparse.Namespace) -> int:
    cases = load_cases()
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=args.chunking)
    strategy_spans = chunk_token_spans(index)
    heading_index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    heading_spans = chunk_token_spans(heading_index)
    heading_by_id = {chunk.id: chunk for chunk in heading_index.chunks}
    adjudications = load_adjudications(args.adjudications)
    embedding_adjudications = {
        (row["case_id"], row["chunk_id"]): row
        for row in load_jsonl(args.embedding_adjudications)
    }
    if args.reuse_results:
        rows = load_jsonl(args.cases_output)
        case_by_id = {case.case_id: case for case in cases}
        chunk_by_id = {chunk.id: chunk for chunk in index.chunks}
        for row in rows:
            case = case_by_id[row["case_id"]]
            useful_heading = [heading_by_id[chunk_id] for chunk_id in case.known_useful_chunk_ids if chunk_id in heading_by_id]
            flags = []
            for chunk_id in row["returned_chunk_ids"]:
                embedding_adjudication = embedding_adjudications.get((case.case_id, chunk_id))
                adjudication = adjudications.get((args.chunking, case.case_id, chunk_id))
                if embedding_adjudication is not None:
                    flags.append(bool(embedding_adjudication["useful"]))
                elif adjudication is not None:
                    flags.append(bool(adjudication["useful"]))
                else:
                    flags.append(
                        transferred_label(
                            chunk_by_id[chunk_id],
                            useful_heading,
                            candidate_span=strategy_spans[chunk_id],
                            heading_spans=heading_spans,
                            exact_heading_ids=set(case.known_useful_chunk_ids),
                            strategy=args.chunking,
                        )[0]
                    )
            useful_ids = [chunk_id for chunk_id, useful in zip(row["returned_chunk_ids"], flags, strict=True) if useful]
            ranks = [rank for rank, useful in enumerate(flags, start=1) if useful]
            row["useful_returned_chunk_ids"] = useful_ids
            row["useful_result_count"] = len(useful_ids)
            row["first_useful_rank"] = min(ranks) if ranks else None
    else:
        client = OpenAIEmbeddingClient()
        store = PineconeVectorStore.from_env()
        rows = []
        jobs: list[tuple[Case, str, tuple[str | None, ...] | None]] = []
        for case in cases:
            if args.policy in {"both", "single"}:
                jobs.append((case, "single", (args.single_namespace,)))
            if args.policy in {"both", "subject_oracle"}:
                jobs.append(
                    (
                        case,
                        "subject_oracle",
                        tuple(subject_namespaces(case.oracle_subjects, prefix=args.namespace_prefix)),
                    )
                )

        def execute(job: tuple[Case, str, tuple[str | None, ...] | None]) -> dict[str, Any]:
            case, policy, namespaces = job
            return pinecone_case(
                case,
                index=index,
                client=client,
                store=store,
                namespaces=namespaces,
                policy=policy,
                top_k=args.top_k,
                namespace_prefix=args.namespace_prefix,
                strategy_spans=strategy_spans,
                heading_spans=heading_spans,
                heading_by_id=heading_by_id,
                strategy=args.chunking,
                adjudications=adjudications,
                embedding_adjudications=embedding_adjudications,
            )

        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            for row in executor.map(execute, jobs):
                print(f"{row['policy']} {row['case_id']} {row['latency_ms']}ms", file=sys.stderr)
                rows.append(row)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["policy"], []).append(row)

    summaries = {policy: summarize(policy_rows, top_k=args.top_k) for policy, policy_rows in grouped.items()}
    ranking_parity = None
    if "single" in grouped and "subject_oracle" in grouped:
        single_by_case = {row["case_id"]: row for row in grouped["single"]}
        oracle_by_case = {row["case_id"]: row for row in grouped["subject_oracle"]}
        ranking_parity = sum(
            single_by_case[case_id]["returned_chunk_ids"] == oracle_by_case[case_id]["returned_chunk_ids"]
            for case_id in single_by_case
        )
    summary = {
        "experiment": "active-query-pinecone-revalidation",
        "cases": len(cases),
        "query_writer": f"{MODEL}/{METHOD}",
        "chunking": args.chunking,
        "retriever": "Pinecone hybrid, one query per case",
        "max_workers": args.max_workers,
        "ranking_parity_cases": ranking_parity,
        "conditions": summaries,
    }
    write_json(args.summary, summary)
    write_jsonl(args.cases_output, rows)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    chunking = subparsers.add_parser("chunking", help="Compare chunking strategies under local hybrid retrieval.")
    chunking.add_argument("--strategies", nargs="+", choices=tuple(CHUNKING_STRATEGIES), default=list(CHUNKING_STRATEGIES))
    chunking.add_argument("--top-k", type=int, default=5)
    chunking.add_argument("--summary", type=Path, default=REPORT_DIR / "active_query_chunking_revalidation_summary.json")
    chunking.add_argument("--cases-output", type=Path, default=REPORT_DIR / "active_query_chunking_revalidation_cases.jsonl")
    chunking.add_argument("--adjudications", type=Path, default=DEFAULT_ADJUDICATIONS)
    chunking.set_defaults(func=run_chunking)

    matrix = subparsers.add_parser(
        "matrix",
        help="Replay the full frozen query/model/retriever matrix on the active chunks.",
    )
    matrix.add_argument("--top-k", type=int, default=5)
    matrix.add_argument("--chunking", choices=tuple(CHUNKING_STRATEGIES), default="framework-aware")
    matrix.add_argument(
        "--summary",
        type=Path,
        default=REPORT_DIR / "active_framework_retrieval_matrix_summary.json",
    )
    matrix.add_argument(
        "--cases-output",
        type=Path,
        default=REPORT_DIR / "active_framework_retrieval_matrix_cases.jsonl",
    )
    matrix.add_argument("--adjudications", type=Path, default=DEFAULT_ADJUDICATIONS)
    matrix.set_defaults(func=run_matrix)

    pinecone = subparsers.add_parser("pinecone", help="Compare Pinecone single and oracle subject namespace layouts.")
    pinecone.add_argument("--top-k", type=int, default=5)
    pinecone.add_argument("--namespace-prefix", default="money-models")
    pinecone.add_argument("--single-namespace", default=ACTIVE_PINECONE_NAMESPACE)
    pinecone.add_argument("--chunking", choices=tuple(CHUNKING_STRATEGIES), default="framework-aware")
    pinecone.add_argument("--max-workers", type=int, default=1)
    pinecone.add_argument("--policy", choices=("both", "single", "subject_oracle"), default="both")
    pinecone.add_argument("--reuse-results", action="store_true", help="Rescore the saved result IDs without querying Pinecone.")
    pinecone.add_argument("--summary", type=Path, default=REPORT_DIR / "active_query_pinecone_revalidation_summary.json")
    pinecone.add_argument("--cases-output", type=Path, default=REPORT_DIR / "active_query_pinecone_revalidation_cases.jsonl")
    pinecone.add_argument("--adjudications", type=Path, default=DEFAULT_ADJUDICATIONS)
    pinecone.add_argument("--embedding-adjudications", type=Path, default=DEFAULT_EMBEDDING_ADJUDICATIONS)
    pinecone.set_defaults(func=run_pinecone)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
