#!/usr/bin/env python3
"""Audit query realism and lexical overlap with framework/chapter names."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import tokenize  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def chapter_terms(transcript_dir: Path) -> dict[str, set[str]]:
    terms = {}
    for path in sorted(transcript_dir.glob("*.txt")):
        terms[path.stem] = set(tokenize(path.stem.replace("-", " ")))
    return terms


def phrase_present(query: str, chapter: str) -> bool:
    return " ".join(tokenize(chapter.replace("-", " "))) in " ".join(tokenize(query))


def overlap_score(query: str, terms: set[str]) -> float:
    query_terms = set(tokenize(query))
    if not terms:
        return 0.0
    return len(query_terms & terms) / len(terms)


def score_query(row: dict[str, Any], terms_by_chapter: dict[str, set[str]]) -> dict[str, Any]:
    overlaps = {
        chapter: overlap_score(row["query"], terms)
        for chapter, terms in terms_by_chapter.items()
    }
    phrase_hits = [
        chapter
        for chapter in terms_by_chapter
        if phrase_present(row["query"], chapter)
    ]
    best_chapter, best_overlap = max(overlaps.items(), key=lambda item: item[1])
    candidate_chapters = row.get("candidate_chapters") or row.get("must_chapters") or []
    candidate_phrase_hits = [
        chapter
        for chapter in candidate_chapters
        if chapter in terms_by_chapter and phrase_present(row["query"], chapter)
    ]
    candidate_overlaps = [
        overlap_score(row["query"], terms_by_chapter[chapter])
        for chapter in candidate_chapters
        if chapter in terms_by_chapter
    ]
    return {
        "id": row["id"],
        "query": row["query"],
        "query_type": row.get("query_type", "pilot"),
        "candidate_chapters": candidate_chapters,
        "best_overlap_chapter": best_chapter,
        "best_chapter_name_overlap": round(best_overlap, 4),
        "any_chapter_phrase_hit": bool(phrase_hits),
        "chapter_phrase_hits": phrase_hits,
        "candidate_chapter_phrase_hit": bool(candidate_phrase_hits),
        "candidate_chapter_phrase_hits": candidate_phrase_hits,
        "max_candidate_chapter_overlap": round(max(candidate_overlaps), 4) if candidate_overlaps else 0.0,
    }


def summarize(name: str, rows: list[dict[str, Any]], terms_by_chapter: dict[str, set[str]]) -> dict[str, Any]:
    scored = [score_query(row, terms_by_chapter) for row in rows]
    overlaps = [row["best_chapter_name_overlap"] for row in scored]
    candidate_overlaps = [row["max_candidate_chapter_overlap"] for row in scored]
    return {
        "name": name,
        "total": len(scored),
        "query_type_counts": dict(Counter(row["query_type"] for row in scored)),
        "avg_best_chapter_name_overlap": round(statistics.mean(overlaps), 4) if overlaps else 0.0,
        "avg_candidate_chapter_overlap": round(statistics.mean(candidate_overlaps), 4) if candidate_overlaps else 0.0,
        "chapter_phrase_hit_rate": round(sum(row["any_chapter_phrase_hit"] for row in scored) / len(scored), 4) if scored else 0.0,
        "candidate_phrase_hit_rate": round(sum(row["candidate_chapter_phrase_hit"] for row in scored) / len(scored), 4) if scored else 0.0,
        "queries": scored,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Query Realism Methodology",
        "",
        "## Purpose",
        "",
        "The original `evals/golden.jsonl` set is a pilot set. It is useful for validating that the retrieval harness runs, but many queries name the same frameworks used in the corpus. That can inflate lexical retrieval results because BM25 is rewarded when the query repeats chapter titles or framework names.",
        "",
        "The next retrieval benchmark should use realistic user-intent queries before selecting a dense, hybrid, fusion, or rerank strategy.",
        "",
        "## Query Types",
        "",
        "The draft realistic set lives in `evals/realistic_queries.jsonl`.",
        "",
        "| Query Type | Purpose |",
        "|---|---|",
        "| `exact_framework` | Keeps a small number of direct framework-name lookups so named concepts still work. |",
        "| `paraphrase` | Tests whether retrieval finds the right concept when the user describes it without naming it. |",
        "| `business_situation` | Tests messy business context where the user describes symptoms, not frameworks. |",
        "| `diagnostic_numeric` | Tests whether unit-economics questions retrieve the right metric and diagnostic material. |",
        "| `confusable` | Tests near-neighbor concepts that are easy to mix up, such as payment plans vs feature downsells. |",
        "| `noisy_vague` | Tests realistic typos, shorthand, incomplete phrasing, and casual user language. |",
        "",
        "## Lexical-Overlap Audit",
        "",
        "| Dataset | Queries | Type Mix | Avg Best Chapter-Name Overlap | Avg Candidate Chapter Overlap | Any Chapter Phrase Hit | Candidate Phrase Hit |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for dataset in run["datasets"]:
        type_mix = ", ".join(f"{name}: {count}" for name, count in sorted(dataset["query_type_counts"].items()))
        lines.append(
            f"| `{dataset['name']}` | {dataset['total']} | {type_mix} | "
            f"{dataset['avg_best_chapter_name_overlap']:.2%} | {dataset['avg_candidate_chapter_overlap']:.2%} | "
            f"{dataset['chapter_phrase_hit_rate']:.2%} | {dataset['candidate_phrase_hit_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "Interpretation: lower overlap is not automatically better; exact-framework queries should overlap. The purpose is to make the benchmark mix explicit so lexical lookup does not dominate the final retrieval decision.",
            "",
            "## Highest Candidate-Overlap Queries",
            "",
        ]
    )
    for dataset in run["datasets"]:
        lines.append(f"### {dataset['name']}")
        lines.append("")
        highest = sorted(dataset["queries"], key=lambda row: row["max_candidate_chapter_overlap"], reverse=True)[:8]
        for row in highest:
            lines.append(
                f"- `{row['id']}` ({row['query_type']}): candidate overlap {row['max_candidate_chapter_overlap']:.2%}; "
                f"candidate phrase hit: {row['candidate_chapter_phrase_hit']}; query: {row['query']}"
            )
        lines.append("")

    lines.extend(
        [
            "## Labeling Rule",
            "",
            "The fields `target_layer_hint` and `candidate_chapters` are reviewer orientation only. They are not final relevance labels.",
            "",
            "Final retrieval selection should use chunk-level judgments:",
            "",
            "| Label | Meaning |",
            "|---:|---|",
            "| 0 | The chunk is not useful for answering this query. |",
            "| 1 | The chunk is partially useful or background context, but not enough by itself. |",
            "| 2 | The chunk directly supports a good answer to the query. |",
            "",
            "## Evaluation Procedure",
            "",
            "1. Run each candidate retriever against the same realistic query set.",
            "2. For each query, collect the top chunks returned by every candidate.",
            "3. Dedupe by chunk ID.",
            "4. Hide which retriever returned each chunk before review.",
            "5. Label each query/chunk pair with the 0/1/2 rubric.",
            "6. Score each retriever by the relevance grades of the chunks it ranked highly.",
            "",
            "## Decision Rule",
            "",
            "Do not select a final retriever from the pilot chapter-level metrics.",
            "",
            "Use the pilot results only to show that the harness works and to identify candidate retrievers. Use realistic-query, chunk-level relevance judgments to choose among dense, hybrid, fusion, and rerank variants.",
            "",
            "## Current Status",
            "",
            "- Pilot query set: `evals/golden.jsonl`",
            "- Draft realistic query set: `evals/realistic_queries.jsonl`",
            "- Old keyword evidence experiments: `archive/keyword-evidence-proxy/`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit query realism")
    parser.add_argument("--pilot", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--realistic", type=Path, default=ROOT / "evals" / "realistic_queries.jsonl")
    parser.add_argument("--transcripts", type=Path, default=ROOT / "corpus" / "transcripts")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "query_realism.md")
    args = parser.parse_args()

    terms_by_chapter = chapter_terms(args.transcripts)
    run = {
        "datasets": [
            summarize("pilot-golden", load_jsonl(args.pilot), terms_by_chapter),
            summarize("realistic-draft", load_jsonl(args.realistic), terms_by_chapter),
        ]
    }
    write_report(run, args.report)
    print(json.dumps({dataset["name"]: {key: dataset[key] for key in ("total", "query_type_counts", "avg_candidate_chapter_overlap", "candidate_phrase_hit_rate")} for dataset in run["datasets"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
