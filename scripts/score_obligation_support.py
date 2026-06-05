#!/usr/bin/env python3
"""Score retrieval by human-audited required-supported-claim labels."""

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
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def golden_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in load_jsonl(path)}


def load_obligations(path: Path, include_proposed: bool) -> list[dict[str, Any]]:
    allowed = {"accepted", "proposed"} if include_proposed else {"accepted"}
    return [
        obligation
        for obligation in load_jsonl(path)
        if obligation.get("status") in allowed and obligation.get("supporting_chunk_ids")
    ]


def score_obligation(index: CorpusIndex, golden: dict[str, dict[str, Any]], obligation: dict[str, Any], top_k: int) -> dict[str, Any]:
    record = golden[obligation["record_id"]]
    started = time.perf_counter()
    results = index.search(record["query"], layer=record.get("layer"), top_k=top_k)
    latency_ms = (time.perf_counter() - started) * 1000
    retrieved_ids = [result.chunk.id for result in results]
    supporting = set(obligation["supporting_chunk_ids"])
    matched = [chunk_id for chunk_id in retrieved_ids if chunk_id in supporting]
    return {
        "id": obligation["id"],
        "record_id": obligation["record_id"],
        "claim": obligation["claim"],
        "status": obligation.get("status"),
        "supporting_chunk_ids": obligation["supporting_chunk_ids"],
        "retrieved_chunk_ids": retrieved_ids,
        "supported": bool(matched),
        "matched_chunk_ids": matched,
        "latency_ms": round(latency_ms, 3),
    }


def evaluate(obligations: list[dict[str, Any]], golden: dict[str, dict[str, Any]], chunking: str, top_k: int) -> dict[str, Any]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking=chunking)
    query_results = [score_obligation(index, golden, obligation, top_k) for obligation in obligations]
    total = len(query_results)
    supported = sum(1 for result in query_results if result["supported"])
    latencies = [result["latency_ms"] for result in query_results]
    return {
        "strategy": f"bm25-{chunking}",
        "metrics": {
            "total": total,
            "obligation_support_coverage": round(supported / total, 4) if total else 0.0,
            "unsupported": total - supported,
            "p50_latency_ms": round(statistics.median(latencies), 3) if latencies else 0.0,
        },
        "obligations": query_results,
    }


def write_report(run: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Required Claim Support Coverage",
        "",
        "## Hypothesis",
        "",
        "Retrieval should return chunks that support the required claims a human expects for each eval query.",
        "",
        "## Label Set",
        "",
        f"- Label status included: `{run['label_status']}`",
        f"- Required-claim labels scored: {run['metrics']['total']}",
        "",
        "## Results",
        "",
        "| Strategy | Required Claims | Support Coverage | Unsupported | p50 Latency |",
        "|---|---:|---:|---:|---:|",
        f"| `{run['strategy']}` | {run['metrics']['total']} | {run['metrics']['obligation_support_coverage']:.2%} | {run['metrics']['unsupported']} | {run['metrics']['p50_latency_ms']} ms |",
        "",
        "## Unsupported Required Claims",
        "",
    ]
    misses = [item for item in run["obligations"] if not item["supported"]]
    if not misses:
        lines.append("- None.")
    else:
        for miss in misses:
            lines.append(f"- `{miss['id']}`: {miss['claim']}")
            lines.append(f"  Expected one of: {', '.join(f'`{chunk_id}`' for chunk_id in miss['supporting_chunk_ids'])}")
            lines.append(f"  Retrieved: {', '.join(f'`{chunk_id}`' for chunk_id in miss['retrieved_chunk_ids'])}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use accepted required-claim support coverage as the primary retrieval-support guardrail.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score obligation support coverage")
    parser.add_argument("--golden", type=Path, default=ROOT / "evals" / "golden.jsonl")
    parser.add_argument("--obligations", type=Path, default=ROOT / "evals" / "obligations.jsonl")
    parser.add_argument("--include-proposed", action="store_true")
    parser.add_argument("--chunking", default="heading-aware")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "obligation_support_coverage.md")
    args = parser.parse_args()

    golden = golden_by_id(args.golden)
    obligations = load_obligations(args.obligations, include_proposed=args.include_proposed)
    report_path = args.report
    default_report = ROOT / "evals" / "reports" / "obligation_support_coverage.md"
    if args.include_proposed and args.report == default_report:
        report_path = ROOT / "evals" / "reports" / "obligation_support_coverage_proposed.md"

    run = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
        "experiment": "obligation-support-coverage",
        "dataset": str(args.obligations.relative_to(ROOT)),
        "label_status": "accepted+proposed" if args.include_proposed else "accepted",
        **evaluate(obligations, golden, args.chunking, args.top_k),
    }
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    run_path = args.runs_dir / f"{run['run_id']}-obligation-support-coverage.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    write_report(run, report_path)
    print(json.dumps({"run_path": str(run_path.relative_to(ROOT)), "report_path": str(report_path.relative_to(ROOT)), **run["metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
