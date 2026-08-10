#!/usr/bin/env python3
"""Three-way query-generation comparison: keyword-only vs variants-only vs RAG-fusion.

Reuses the search-query-quality harness. Scores each method against whatever
answer key is in --cases (pass the enriched-labels file to match the §3.5 grade).
No model calls. Embeddings, when the backend needs them, are read from cache;
the run aborts if any query embedding is cold so this never spends API budget by
surprise.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import eval_search_query_quality as eq  # noqa: E402

METHODS = {
    "keyword_only": "generated",
    "variants_only": "generated_variants_only",
    "rag_fusion": "generated_variants",
}


def summarize(results):
    n = len(results)
    hit1 = sum(1 for r in results if r.known_useful_rank == 1)
    hit3 = sum(1 for r in results if r.useful_at_3)
    hit5 = sum(1 for r in results if r.useful_at_5)
    ranks = [r.known_useful_rank for r in results if r.known_useful_rank is not None]
    mean_rank = sum(ranks) / len(ranks) if ranks else None
    return {
        "n": n,
        "hit1": hit1,
        "hit1_pct": round(100 * hit1 / n, 1),
        "hit3_pct": round(100 * hit3 / n, 1),
        "hit5_pct": round(100 * hit5 / n, 1),
        "mean_useful_rank": round(mean_rank, 3) if mean_rank is not None else None,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_search_query_cases_enriched_labels.jsonl")
    p.add_argument("--query-variants", type=Path, default=ROOT / "evals" / "advisor_query_variants_v2.jsonl")
    p.add_argument("--backend", choices=("bm25", "vector", "hybrid"), default="bm25")
    p.add_argument("--vector-store", choices=("local", "pinecone"), default="local")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--max-workers", type=int, default=1)
    args = p.parse_args()

    cases = eq.load_jsonl(args.cases)
    errors = eq.validate_cases(cases)
    if errors:
        print(json.dumps({"validation_errors": errors}, indent=2))
        return 1
    variants = eq.load_variant_rows(args.query_variants)

    per_method = {}
    embedding_meta = {}
    for name, source in METHODS.items():
        results, meta = eq.score_cases_with_metrics(
            cases,
            top_k=args.top_k,
            query_source=source,
            retrieval_backend=args.backend,
            variants_by_case=variants,
            vector_store_name=args.vector_store,
            max_workers=args.max_workers,
        )
        per_method[name] = {r.case_id: r for r in results}
        embedding_meta[name] = meta.get("embedding")

    # Per-case attribution: where do variants-only and rag-fusion diverge, and
    # does the appended keyword query ever change the Hit@1 outcome?
    keyword = per_method["keyword_only"]
    variants_only = per_method["variants_only"]
    fusion = per_method["rag_fusion"]

    diffs = []
    for cid in variants_only:
        vr = variants_only[cid].known_useful_rank
        fr = fusion[cid].known_useful_rank
        kr = keyword[cid].known_useful_rank
        v_hit1 = vr == 1
        f_hit1 = fr == 1
        if v_hit1 != f_hit1 or vr != fr:
            diffs.append({
                "case": cid,
                "keyword_rank": kr,
                "variants_only_rank": vr,
                "rag_fusion_rank": fr,
                "effect": (
                    "fusion_better" if (f_hit1 and not v_hit1)
                    else "fusion_worse" if (v_hit1 and not f_hit1)
                    else "rank_shift_same_hit1"
                ),
            })

    # Cases the keyword query gets at Hit@1 that variants-only misses (would
    # justify a floor), and vice versa.
    keyword_rescues = [cid for cid in variants_only
                       if keyword[cid].known_useful_rank == 1 and (variants_only[cid].known_useful_rank or 99) != 1]
    variants_beat_keyword = [cid for cid in variants_only
                             if variants_only[cid].known_useful_rank == 1 and (keyword[cid].known_useful_rank or 99) != 1]

    out = {
        "backend": args.backend,
        "vector_store": args.vector_store if args.backend in {"vector", "hybrid"} else "n/a",
        "cases_file": str(args.cases.relative_to(ROOT)),
        "summary": {name: summarize(list(m.values())) for name, m in per_method.items()},
        "fusion_vs_variants_only_diffs": diffs,
        "keyword_hit1_that_variants_only_miss": keyword_rescues,
        "variants_only_hit1_that_keyword_miss": variants_beat_keyword,
        "embedding": embedding_meta if args.backend in {"vector", "hybrid"} else "n/a (bm25)",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
