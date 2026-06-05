#!/usr/bin/env python3
"""Score whether retrieved chunks contain hand-labeled citation evidence terms."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import CorpusIndex  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("evidence_terms"):
                    records.append(record)
    return records


def normalize(text: str) -> str:
    normalized = text.lower().replace("-", " ")
    replacements = {
        " zero ": " 0 ",
        " one ": " 1 ",
        " two ": " 2 ",
        " three ": " 3 ",
        " four ": " 4 ",
        " five ": " 5 ",
        " six ": " 6 ",
        " seven ": " 7 ",
        " eight ": " 8 ",
        " nine ": " 9 ",
        " ten ": " 10 ",
        " thirty ": " 30 ",
    }
    normalized = f" {normalized} "
    for word, digit in replacements.items():
        normalized = normalized.replace(word, digit)
    return " ".join(normalized.split())


def term_present(text: str, term: str) -> bool:
    return normalize(term) in normalize(text)


def score_record(index: CorpusIndex, record: dict[str, Any], top_k: int) -> dict[str, Any]:
    started = time.perf_counter()
    results = index.search(record["query"], layer=record.get("layer"), top_k=top_k)
    latency_ms = (time.perf_counter() - started) * 1000

    expected = set(record["must_chapters"])
    expected_results = [result for result in results if result.chunk.chapter in expected]
    terms = record["evidence_terms"]
    scored_chunks = []
    for result in expected_results or results[:1]:
        present_for_chunk = [term for term in terms if term_present(result.chunk.text, term)]
        scored_chunks.append((len(present_for_chunk), result.chunk, present_for_chunk))
    _score, evidence_chunk, present = max(scored_chunks, key=lambda item: item[0]) if scored_chunks else (0, None, [])
    missing = [term for term in terms if term not in present]

    return {
        "id": record["id"],
        "layer": record.get("layer"),
        "expected_chapters": record["must_chapters"],
        "evidence_chunk": evidence_chunk.id if evidence_chunk else None,
        "evidence_chapter": evidence_chunk.chapter if evidence_chunk else None,
        "retrieved_chapters": [result.chunk.chapter for result in results],
        "terms_total": len(terms),
        "terms_present": len(present),
        "coverage": round(len(present) / len(terms), 4) if terms else 0.0,
        "present": present,
        "missing": missing,
        "latency_ms": round(latency_ms, 3),
    }


def evaluate(records: list[dict[str, Any]], strategy: str, top_k: int) -> dict[str, Any]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=strategy)
    query_results = [score_record(index, record, top_k) for record in records]
    coverages = [result["coverage"] for result in query_results]
    full = sum(1 for result in query_results if result["coverage"] == 1.0)
    return {
        "strategy": strategy,
        "chunks": len(index.chunks),
        "avg_chunk_words": round(index.average_chunk_words(), 1),
        "metrics": {
            "total": len(query_results),
            "avg_coverage": round(statistics.mean(coverages), 4) if coverages else 0.0,
            "full_coverage_rate": round(full / len(query_results), 4) if query_results else 0.0,
            "min_coverage": round(min(coverages), 4) if coverages else 0.0,
        },
        "queries": query_results,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    variants = run["variants"]
    best = max(variants, key=lambda variant: (variant["metrics"]["avg_coverage"], variant["metrics"]["full_coverage_rate"]))
    baseline = next((variant for variant in variants if variant["strategy"] == "heading-aware"), variants[0])
    avg_delta = best["metrics"]["avg_coverage"] - baseline["metrics"]["avg_coverage"]
    full_delta = best["metrics"]["full_coverage_rate"] - baseline["metrics"]["full_coverage_rate"]
    clears_adoption_threshold = best["strategy"] == baseline["strategy"] or avg_delta >= 0.05 or full_delta >= 0.10
    adopted = best if clears_adoption_threshold else baseline

    lines = [
        "# Citation Completeness",
        "",
        "## Hypothesis",
        "",
        "A chunking strategy may be worth adopting even when retrieval rank barely improves if its retrieved chunks contain more complete citation evidence for the final answer.",
        "",
        "## Variants",
        "",
        "| Strategy | Labeled Queries | Avg Coverage | Full Coverage | Min Coverage | Chunks | Avg Words |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in variants:
        metrics = variant["metrics"]
        lines.append(
            f"| `{variant['strategy']}` | {metrics['total']} | {metrics['avg_coverage']:.2%} | "
            f"{metrics['full_coverage_rate']:.2%} | {metrics['min_coverage']:.2%} | {variant['chunks']} | {variant['avg_chunk_words']} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{best['strategy']}` is the metric winner on evidence coverage. The adopted default is `{adopted['strategy']}` because adoption requires at least +5 percentage points average coverage or +10 percentage points full-coverage rate over `heading-aware`.",
            "",
            f"Measured delta vs `heading-aware`: avg coverage {avg_delta:+.2%}, full coverage {full_delta:+.2%}.",
            "",
            "## Per-query Misses",
            "",
        ]
    )

    for variant in variants:
        misses = [query for query in variant["queries"] if query["coverage"] < 1.0]
        lines.append(f"### `{variant['strategy']}`")
        if not misses:
            lines.append("")
            lines.append("- No missing evidence terms.")
            lines.append("")
            continue
        lines.append("")
        for miss in misses:
            missing = ", ".join(f"`{term}`" for term in miss["missing"])
            lines.append(f"- `{miss['id']}` coverage {miss['coverage']:.2%}; missing {missing}.")
        lines.append("")

    lines.extend(
        [
            "## Next Experiment",
            "",
            "Move to retrieval ablation: BM25-only vs dense-only vs hybrid. Keep citation completeness as a guardrail so better rank does not come at the cost of weaker evidence chunks.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare citation evidence completeness by chunking strategy")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "citation_completeness.md")
    parser.add_argument("--strategies", nargs="*", default=["heading-aware", "framework-aware"])
    args = parser.parse_args()

    records = load_jsonl(args.golden)
    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "experiment": "citation-completeness",
        "dataset": str(args.golden.relative_to(ROOT)),
        "top_k": args.top_k,
        "variants": [evaluate(records, strategy, args.top_k) for strategy in args.strategies],
    }
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-citation-completeness.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, args.report)
    print(
        json.dumps(
            {
                "run_path": str(run_path.relative_to(ROOT)),
                "report_path": str(args.report.relative_to(ROOT)),
                "variants": [
                    {"strategy": variant["strategy"], **variant["metrics"]}
                    for variant in run["variants"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
