#!/usr/bin/env python3
"""Audit evidence-term labels used by citation-completeness evals."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import tokenize  # noqa: E402


GENERIC_SINGLE_TERMS = {
    "cac",
    "upsell",
    "service",
    "revenue",
    "month",
    "cancel",
    "free",
    "bonus",
    "feature",
    "customer",
    "offer",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("evidence_terms"):
                    records.append(record)
    return records


def normalized_contains(text: str, term: str) -> bool:
    normalized_text = " ".join(tokenize(text))
    normalized_term = " ".join(tokenize(term))
    return bool(normalized_term) and normalized_term in normalized_text


def chapter_contains_tokens(chapter_tokens: set[str], term: str) -> bool:
    term_tokens = set(tokenize(term))
    return bool(term_tokens) and term_tokens <= chapter_tokens


def audit(records: list[dict[str, Any]], transcripts: dict[str, str]) -> list[dict[str, Any]]:
    chapter_tokens = {chapter: set(tokenize(text)) for chapter, text in transcripts.items()}
    output = []
    for record in records:
        expected_text = "\n".join(transcripts.get(chapter, "") for chapter in record["must_chapters"])
        absent = [term for term in record["evidence_terms"] if not normalized_contains(expected_text, term)]
        generic = []
        for term in record["evidence_terms"]:
            term_tokens = set(tokenize(term))
            chapter_count = sum(1 for tokens in chapter_tokens.values() if chapter_contains_tokens(tokens, term))
            is_generic_single = len(term_tokens) == 1 and next(iter(term_tokens), "") in GENERIC_SINGLE_TERMS
            if chapter_count >= 8 or is_generic_single:
                generic.append({"term": term, "chapter_count": chapter_count})
        output.append(
            {
                "id": record["id"],
                "must_chapters": record["must_chapters"],
                "terms": record["evidence_terms"],
                "absent_from_expected_chapters": absent,
                "possibly_generic_terms": generic,
            }
        )
    return output


def write_report(rows: list[dict[str, Any]], report_path: Path) -> None:
    absent_count = sum(len(row["absent_from_expected_chapters"]) for row in rows)
    generic_count = sum(len(row["possibly_generic_terms"]) for row in rows)
    lines = [
        "# Evidence Term Label Audit",
        "",
        "## Purpose",
        "",
        "Evidence-term coverage is a cheap proxy for whether retrieved chunks contain answer-supporting details. It is not a final faithfulness score. This audit checks whether labels are source-present and flags labels that may be too generic to support decision-grade conclusions.",
        "",
        "## Summary",
        "",
        f"- Labeled records: {len(rows)}",
        f"- Terms absent from expected chapters: {absent_count}",
        f"- Possibly generic terms: {generic_count}",
        "",
        "## Findings",
        "",
        "| Record | Absent Terms | Possibly Generic Terms |",
        "|---|---|---|",
    ]
    for row in rows:
        absent = ", ".join(f"`{term}`" for term in row["absent_from_expected_chapters"]) or "-"
        generic = ", ".join(f"`{item['term']}` ({item['chapter_count']} chapters)" for item in row["possibly_generic_terms"]) or "-"
        lines.append(f"| `{row['id']}` | {absent} | {generic} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Treat citation-completeness results as provisional until the evidence terms are manually reviewed against the transcript spans they are meant to support. Retrieval rank metrics remain valid because they are based on expected chapters, not these proxy labels.",
            "",
            "## Next Labeling Pass",
            "",
            "- Replace generic single-word labels with source-grounded answer facts or short phrases.",
            "- For each labeled query, record why each term is answer-critical.",
            "- Add `required_evidence_spans` or `must_cite_chunks` for the highest-value eval records so citation scoring is not only keyword based.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    records = load_jsonl(ROOT / "evals" / "golden.jsonl")
    transcripts = {path.stem: path.read_text(encoding="utf-8") for path in (ROOT / "corpus" / "transcripts").glob("*.txt")}
    rows = audit(records, transcripts)
    report_path = ROOT / "evals" / "reports" / "evidence_term_label_audit.md"
    write_report(rows, report_path)
    print(
        json.dumps(
            {
                "report_path": str(report_path.relative_to(ROOT)),
                "labeled_records": len(rows),
                "absent_terms": sum(len(row["absent_from_expected_chapters"]) for row in rows),
                "possibly_generic_terms": sum(len(row["possibly_generic_terms"]) for row in rows),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
