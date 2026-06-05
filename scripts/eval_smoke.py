#!/usr/bin/env python3
"""Tiny retrieval smoke eval for the local proof harness.

For full metrics and report generation, run `scripts/eval_retrieval.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import CorpusIndex  # noqa: E402


def main() -> int:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts")
    total = 0
    passed = 0
    failures: list[dict[str, object]] = []

    with (ROOT / "evals" / "golden.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            total += 1
            results = index.search(record["query"], layer=record.get("layer"), top_k=5)
            chapters = [result.chunk.chapter for result in results]
            ok = any(chapter in chapters for chapter in record["must_chapters"])
            passed += int(ok)
            if not ok:
                failures.append(
                    {
                        "id": record["id"],
                        "expected": record["must_chapters"],
                        "actual": chapters,
                    }
                )

    print(json.dumps({"total": total, "passed": passed, "failures": failures}, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
