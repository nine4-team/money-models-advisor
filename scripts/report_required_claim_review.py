#!/usr/bin/env python3
"""Summarize required-claim label review status."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> int:
    rows = load_rows(ROOT / "evals" / "obligations.jsonl")
    status_counts = Counter(row.get("status", "missing") for row in rows)
    attention = [row for row in rows if row.get("status") in {"proposed", "needs_better_chunk", "rejected"}]
    lines = [
        "# Required Claim Review Status",
        "",
        "## Summary",
        "",
        f"- Total labels: {len(rows)}",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: {count}")
    lines.extend(
        [
            "",
            "## Labels Needing Attention",
            "",
        ]
    )
    if not attention:
        lines.append("- None.")
    else:
        for row in attention:
            lines.append(f"- `{row['id']}` ({row.get('status', 'missing')}): {row['claim']}")
            if row.get("notes"):
                lines.append(f"  Notes: {row['notes']}")
    report_path = ROOT / "evals" / "reports" / "required_claim_review_status.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(report_path.relative_to(ROOT)), "total": len(rows), "status_counts": dict(status_counts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
