#!/usr/bin/env python3
"""Validate and summarize the current-path semantic answer audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "evals" / "advisor_answer_quality_audit.jsonl"
RUNS = ROOT / "evals" / "runs" / "source_events" / "search_request_v1"
REPORT = ROOT / "evals" / "reports" / "advisor_answer_quality.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(audits: list[dict[str, Any]], runs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for audit in audits:
        run_path = runs_dir / audit["case_id"] / "run.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        answer_hash = hashlib.sha256(run["assistant_message"].encode()).hexdigest()
        claims = audit["claims"]
        rows.append(
            {
                "case_id": audit["case_id"],
                "current": answer_hash == audit["answer_sha256"],
                "recommendation_correct": bool(audit["recommendation_correct"]),
                "recommendation_useful": bool(audit["recommendation_useful"]),
                "claims": len(claims),
                "supported_claims": sum(bool(claim["supported"]) for claim in claims),
            }
        )
    return rows


def main() -> int:
    audits = load_jsonl(AUDIT)
    rows = evaluate(audits, RUNS)
    current = sum(row["current"] for row in rows)
    total_claims = sum(row["claims"] for row in rows)
    supported = sum(row["supported_claims"] for row in rows)
    lines = [
        "# Advisor Answer-Quality Audit",
        "",
        "## Method",
        "",
        "Codex reviewed the six frozen current-path answers against the saved snapshot, user turn, and exact cited passages. The audit checks whether the recommendation is reasonable and useful and whether each material source-backed claim is supported by its cited text. Answer hashes prevent a changed answer from inheriting an old judgment.",
        "",
        "## Results",
        "",
        f"- Current audited answers: {current} / {len(rows)}",
        f"- Correct recommendations: {sum(row['recommendation_correct'] for row in rows)} / {len(rows)}",
        f"- Useful recommendations: {sum(row['recommendation_useful'] for row in rows)} / {len(rows)}",
        f"- Supported source-backed claims: {supported} / {total_claims}",
        "",
        "| Case | Current audit | Correct | Useful | Supported claims |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['case_id']}` | {'yes' if row['current'] else 'no'} | "
            f"{'yes' if row['recommendation_correct'] else 'no'} | "
            f"{'yes' if row['recommendation_useful'] else 'no'} | "
            f"{row['supported_claims']} / {row['claims']} |"
        )
    lines.extend(
        [
            "",
            "## Corrections Found",
            "",
            "The first audit found two unsupported or overstated formulations: a front-end offer was described as necessarily paid, and a continuity answer attached citations to wording stronger than the passages supported. The operating skill now requires a claim-by-claim support check before `session finish`. Those two cases and one additional citation-specific case were rerun blind; the current answers pass both the source-event scorer and this semantic audit.",
            "",
            "## Scope",
            "",
            "This is a six-case, single-reviewer regression, not a population estimate. Codex performed the semantic review; the deterministic runtime still enforces citation provenance and calculation correctness, while this eval measures semantic support and recommendation quality.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "current": current, "claims": total_claims, "supported": supported, "report": str(REPORT.relative_to(ROOT))}, indent=2))
    return 0 if current == len(rows) and supported == total_claims else 1


if __name__ == "__main__":
    raise SystemExit(main())
