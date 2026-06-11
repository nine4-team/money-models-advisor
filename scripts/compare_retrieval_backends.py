#!/usr/bin/env python3
"""Compare BM25, vector, and hybrid retrieval on the search-query seed cases."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import eval_search_query_quality as query_eval  # noqa: E402
from money_model_architect.embeddings import EmbeddingError  # noqa: E402


BACKENDS = ("bm25", "vector", "hybrid")


def pct(count: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{(count / total) * 100:.1f}%"


def summarize(results: list[query_eval.QueryResult]) -> dict[str, object]:
    total = len(results)
    misses = [result.case_id for result in results if not result.useful_at_5]
    ranks = [result.known_useful_rank for result in results if result.known_useful_rank is not None]
    return {
        "cases": total,
        "known_useful_hit_at_3": pct(sum(result.useful_at_3 for result in results), total),
        "known_useful_hit_at_5": pct(sum(result.useful_at_5 for result in results), total),
        "top1_layer_match": pct(sum(result.top1_layer_match for result in results), total),
        "any_expected_layer_at_5": pct(sum(result.any_layer_match_at_5 for result in results), total),
        "mean_known_useful_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "misses_at_5": misses,
    }


def render_report(query_source: str, top_k: int, summaries: dict[str, dict[str, object]], errors: dict[str, str]) -> str:
    lines = [
        "# Retrieval Backend Comparison",
        "",
        "## Scope",
        "",
        "This report compares retrieval backends after the agent has already generated a SourceNeed and the runtime query builder has generated search text. It does not evaluate whether the agent should search; that is covered by the source-need eval.",
        "",
        f"- Query source: `{query_source}`",
        f"- Top K: `{top_k}`",
        "- Vector backend: OpenAI embeddings with disk cache under `.cache/embeddings/`.",
        "- Hybrid backend: reciprocal-rank fusion over BM25 and vector rankings.",
        "",
        "Known-useful labels are seed relevance labels, not exhaustive judgments. This comparison is useful for engineering direction, not a claim of production retrieval quality.",
        "",
        "## Metrics",
        "",
        "| Backend | Cases | Hit@3 | Hit@5 | Top-1 Layer | Any Expected Layer @5 | Mean Known-Useful Rank | Misses @5 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for backend in BACKENDS:
        if backend in errors:
            lines.append(f"| `{backend}` | - | - | - | - | - | - | {errors[backend]} |")
            continue
        summary = summaries[backend]
        misses = summary["misses_at_5"]
        lines.append(
            "| "
            f"`{backend}` | "
            f"{summary['cases']} | "
            f"{summary['known_useful_hit_at_3']} | "
            f"{summary['known_useful_hit_at_5']} | "
            f"{summary['top1_layer_match']} | "
            f"{summary['any_expected_layer_at_5']} | "
            f"{summary['mean_known_useful_rank'] if summary['mean_known_useful_rank'] is not None else '-'} | "
            f"{', '.join(f'`{case_id}`' for case_id in misses) if misses else 'none'} |"
        )

    lines.extend(
        [
            "",
            "## Dataset",
            "",
        ]
    )
    if summaries:
        any_summary = next(iter(summaries.values()))
        lines.append(f"- Scored cases: {any_summary['cases']}")
    if len(summaries) > 1:
        lines.extend(["", "## Interpretation", ""])
        sorted_hit5 = sorted(
            summaries.items(),
            key=lambda item: (
                _pct_value(item[1]["known_useful_hit_at_5"]),
                -float(item[1]["mean_known_useful_rank"] or 999),
            ),
            reverse=True,
        )
        best_backend, best_summary = sorted_hit5[0]
        lines.append(
            f"- Best eval-slice result by Hit@5 and mean known-useful rank: `{best_backend}` at "
            f"{best_summary['known_useful_hit_at_5']} Hit@5 and mean rank {best_summary['mean_known_useful_rank']}."
        )
        lines.append(
            "- Treat this as a retrieval-engineering signal, not a production benchmark, because the known-useful labels are intentionally non-exhaustive."
        )
        lines.append(
            "- If vector or hybrid underperform BM25 on this eval slice, inspect misses before changing the candidate backend. Dense retrieval may return semantically adjacent chunks while missing exact framework passages the advisor needs to cite."
        )
    if errors:
        lines.extend(["", "## Run Notes", ""])
        for backend, error in errors.items():
            lines.append(f"- `{backend}`: {error}")
    lines.append("")
    return "\n".join(lines)


def _pct_value(value: object) -> float:
    if not isinstance(value, str) or not value.endswith("%"):
        return 0.0
    return float(value[:-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases.jsonl")
    parser.add_argument("--query-source", choices=("reference", "generated", "generated_variants"), default="generated")
    parser.add_argument(
        "--query-variants",
        type=Path,
        default=ROOT / "evals" / "advisor_query_variants_v2.jsonl",
        help="JSONL candidate query variants keyed by case_id; used only with --query-source generated_variants.",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "retrieval_backend_comparison.md")
    parser.add_argument(
        "--require-all-backends",
        action="store_true",
        help="Exit nonzero when vector or hybrid cannot run, for strict backend-comparison gates.",
    )
    args = parser.parse_args()

    cases = query_eval.load_jsonl(args.cases)
    validation_errors = query_eval.validate_cases(cases)
    variants_by_case: dict[str, list[str]] = {}
    if not validation_errors and args.query_source == "generated_variants":
        try:
            variants_by_case = query_eval.load_variant_rows(args.query_variants)
        except ValueError as exc:
            validation_errors.append(str(exc))
        missing_variant_cases = [
            case["case_id"]
            for case in cases
            if case["case_id"] not in variants_by_case
        ]
        if missing_variant_cases:
            validation_errors.append("query variants missing cases: " + ", ".join(missing_variant_cases))
    if validation_errors:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(["# Retrieval Backend Comparison", "", *validation_errors, ""]), encoding="utf-8")
        print(json.dumps({"validation_errors": len(validation_errors), "report": str(args.report)}, indent=2))
        return 1

    summaries: dict[str, dict[str, object]] = {}
    errors: dict[str, str] = {}
    for backend in BACKENDS:
        try:
            results = query_eval.score_cases(
                cases,
                top_k=args.top_k,
                query_source=args.query_source,
                retrieval_backend=backend,
                variants_by_case=variants_by_case,
            )
        except EmbeddingError as exc:
            errors[backend] = str(exc)
            continue
        summaries[backend] = summarize(results)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(args.query_source, args.top_k, summaries, errors), encoding="utf-8")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "query_source": args.query_source,
                "query_variants": str(args.query_variants.resolve().relative_to(ROOT)) if args.query_source == "generated_variants" else None,
                "summaries": summaries,
                "errors": errors,
                "report": str(args.report.resolve().relative_to(ROOT)),
                "split_counts": dict(sorted(Counter(case["split"] for case in cases).items())),
            },
            indent=2,
        )
    )
    return 1 if args.require_all_backends and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
