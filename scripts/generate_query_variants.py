#!/usr/bin/env python3
"""Scaffolding for the query-variant generator comparison.

Purpose: the retrieval comparison (§3.4-3.5) holds the query variants fixed,
which is the right control for comparing retrieval methods but leaves one thing
untested: whether variant *quality* depends on which model wrote them. This
script sets up that experiment without spending anything itself. It has two
modes and never calls a model:

  prompts  Emit one self-contained generation prompt per case (the 30 search
           cases, with their focus terms / subjects / user turn / purpose). A
           subscription coding agent (codex exec, Claude Code) runs these — the
           same cost-clean path §3.8 uses — and writes raw variants back.

  ingest   Take a raw {case_id, query_variants} JSONL a generator produced,
           validate it (2-4 non-empty variants for all 30 cases), and stamp it
           with provenance (model label, generated_at, prompt version) into a
           named variants file the retrieval harness can consume.

Then compare_variant_generators.py runs variants-only retrieval per generator
and tabulates Hit@1 so you can see if the generator moves the number.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_VERSION = "variant-gen-v1"

GENERATION_INSTRUCTION = (
    "You are writing source-material search queries for a Money Models advisor.\n"
    "The advisor has already decided to search and produced a source need:\n"
    "the retrieval purpose, the corpus subjects to search, short focus terms,\n"
    "and the user's turn for context. Write 2-4 short query variants that would\n"
    "retrieve citeable book passages for this need.\n\n"
    "Rules:\n"
    "- Do NOT copy the user's message; phrase the search from source-facing angles.\n"
    "- Vary the phrasing: at least one cause-and-effect phrasing and one that uses\n"
    "  the book's framework vocabulary.\n"
    "- Keep each variant short (a keyword-dense phrase, not a sentence).\n"
    "- Return ONLY a JSON array of strings.\n"
)

CASE_FIELDS = ("case_id", "retrieval_purpose", "expected_subjects", "focus_terms", "user_turn")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_prompts(args: argparse.Namespace) -> int:
    cases = load_jsonl(args.cases)
    prompts = []
    for case in cases:
        spec = {field: case[field] for field in CASE_FIELDS}
        prompts.append({
            "case_id": case["case_id"],
            "prompt_version": PROMPT_VERSION,
            "instruction": GENERATION_INSTRUCTION,
            "source_need": {
                "retrieval_purpose": spec["retrieval_purpose"],
                "subjects": spec["expected_subjects"],
                "focus_terms": spec["focus_terms"],
                "user_turn": spec["user_turn"],
            },
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(p) for p in prompts) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(prompts), "prompt_version": PROMPT_VERSION, "out": str(args.out.relative_to(ROOT))}, indent=2))
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    cases = load_jsonl(args.cases)
    expected_ids = [c["case_id"] for c in cases]
    raw = {row["case_id"]: row.get("query_variants") for row in load_jsonl(args.in_path)}

    errors = []
    for cid in expected_ids:
        variants = raw.get(cid)
        if not isinstance(variants, list) or not (2 <= len(variants) <= 4):
            errors.append(f"{cid}: expected 2-4 variants, got {variants!r}")
            continue
        if not all(isinstance(v, str) and v.strip() for v in variants):
            errors.append(f"{cid}: all variants must be non-empty strings")
    extra = sorted(set(raw) - set(expected_ids))
    if extra:
        errors.append(f"unexpected case_ids not in the 30-case set: {', '.join(extra)}")
    if errors:
        print(json.dumps({"validation_errors": errors}, indent=2))
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for cid in expected_ids:
            fh.write(json.dumps({
                "case_id": cid,
                "query_variants": raw[cid],
                "generator_model": args.model,
                "generated_at": args.generated_at,
                "prompt_version": PROMPT_VERSION,
            }) + "\n")
    print(json.dumps({
        "cases": len(expected_ids),
        "generator_model": args.model,
        "generated_at": args.generated_at,
        "out": str(args.out.relative_to(ROOT)),
    }, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)

    default_cases = ROOT / "evals" / "advisor_search_query_cases.jsonl"

    pp = sub.add_parser("prompts", help="Emit per-case generation prompts for a coding agent to run.")
    pp.add_argument("--cases", type=Path, default=default_cases)
    pp.add_argument("--out", type=Path, default=ROOT / "evals" / "variant_gen_prompts.jsonl")
    pp.set_defaults(func=cmd_prompts)

    pi = sub.add_parser("ingest", help="Validate + stamp a generator's raw variants with provenance.")
    pi.add_argument("--cases", type=Path, default=default_cases)
    pi.add_argument("--in", dest="in_path", type=Path, required=True, help="Raw {case_id, query_variants} JSONL from the generator.")
    pi.add_argument("--model", required=True, help="Generator model label, e.g. gpt-5.4-mini.")
    pi.add_argument("--generated-at", required=True, help="ISO timestamp of the generation run.")
    pi.add_argument("--out", type=Path, required=True, help="Destination provenance-stamped variants file.")
    pi.set_defaults(func=cmd_ingest)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
