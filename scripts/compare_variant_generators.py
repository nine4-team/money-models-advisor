#!/usr/bin/env python3
"""Compare query variants from different generators, holding retrieval fixed.

Runs variants-only retrieval (no keyword fallback) for each provenance-stamped
variants file and tabulates Hit@1 / Hit@3 / mean useful rank against the same
enriched answer key. This isolates the generator: same 30 cases, same backend,
same scorer — only who wrote the variants changes.

Pass generators as label=path pairs. Include the frozen fixture as a baseline:

  python3 scripts/compare_variant_generators.py \\
    frozen_fixture=evals/advisor_query_variants_v2.jsonl \\
    gpt-5.4-mini=evals/advisor_query_variants_gpt_5_4_mini.jsonl

No model calls. Embeddings are read from cache; a cold query embedding raises
rather than silently spending API budget.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import eval_search_query_quality as eq  # noqa: E402


def summarize(results):
    n = len(results)
    hit1 = sum(1 for r in results if r.known_useful_rank == 1)
    hit3 = sum(1 for r in results if r.useful_at_3)
    hit5 = sum(1 for r in results if r.useful_at_5)
    ranks = [r.known_useful_rank for r in results if r.known_useful_rank is not None]
    return {
        "n": n,
        "hit1": hit1,
        "hit1_pct": round(100 * hit1 / n, 1),
        "hit3_pct": round(100 * hit3 / n, 1),
        "hit5_pct": round(100 * hit5 / n, 1),
        "mean_useful_rank": round(sum(ranks) / len(ranks), 3) if ranks else None,
        "misses": [r.case_id for r in results if r.known_useful_rank != 1],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("generators", nargs="+", help="label=path pairs, one per generator.")
    p.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases_enriched_labels.jsonl")
    p.add_argument("--backend", choices=("bm25", "vector", "hybrid"), default="hybrid")
    p.add_argument("--vector-store", choices=("local", "pinecone"), default="local")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()

    pairs = []
    for item in args.generators:
        if "=" not in item:
            print(f"bad generator arg (need label=path): {item}")
            return 2
        label, path = item.split("=", 1)
        pairs.append((label, ROOT / path if not Path(path).is_absolute() else Path(path)))

    cases = eq.load_jsonl(args.cases)
    errors = eq.validate_cases(cases)
    if errors:
        print(json.dumps({"validation_errors": errors}, indent=2))
        return 1

    table = {}
    for label, path in pairs:
        variants = eq.load_variant_rows(path)
        results, _meta = eq.score_cases_with_metrics(
            cases,
            top_k=args.top_k,
            query_source="generated_variants_only",
            retrieval_backend=args.backend,
            variants_by_case=variants,
            vector_store_name=args.vector_store,
        )
        table[label] = summarize(results)

    print(json.dumps({
        "backend": args.backend,
        "vector_store": args.vector_store if args.backend in {"vector", "hybrid"} else "n/a",
        "cases_file": str(args.cases.relative_to(ROOT)),
        "generators": {label: str(path.relative_to(ROOT)) for label, path in pairs},
        "results": table,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
