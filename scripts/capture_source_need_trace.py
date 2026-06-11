#!/usr/bin/env python3
"""Prepare and complete source-need generation trace artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR_NAME = ".money-model-advisor"
SNAPSHOT_FILE = "business_snapshot.json"
SESSIONS_DIR = "sessions"
RUN_FILE = "run.json"

PROMPT_HIDDEN_FIELDS = {
    "split",
    "snapshot_fixture_path",
    "prior_sessions_fixture_path",
    "expected_search",
    "expected_source_need",
    "acceptable_intents",
    "label_rationale",
    "ambiguity",
    "severity_if_wrong",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            record["_line_number"] = line_number
            records.append(record)
    return records


def find_case(cases_path: Path, case_id: str) -> dict[str, Any]:
    for case in load_jsonl(cases_path):
        if case.get("case_id") == case_id:
            return case
    raise SystemExit(f"case not found: {case_id}")


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_session_fixture(source: Path, sessions_dir: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    fixture_id = payload.get("fixture_id", source.stem)
    turns = payload.get("turns")
    if isinstance(turns, list):
        for index, turn in enumerate(turns, 1):
            session = {
                "created_at": turn.get("timestamp"),
                "user_message": turn.get("user_message"),
                "assistant_message": turn.get("assistant_message"),
                "actions": turn.get("actions", []),
                "retrieval_queries": turn.get("retrieval_queries", []),
                "evidence": turn.get("evidence", []),
                "fixture_id": fixture_id,
            }
            write_json(sessions_dir / f"{fixture_id}_{index:02d}.json", session)
        return
    shutil.copy2(source, sessions_dir / source.name)


def prepare_business_dir(case: dict[str, Any], business_dir: Path) -> dict[str, str]:
    state_dir = business_dir / STATE_DIR_NAME
    sessions_dir = state_dir / SESSIONS_DIR
    snapshot_path = state_dir / SNAPSHOT_FILE

    state_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / case["snapshot_fixture_path"], snapshot_path)

    prior_sessions_fixture = case.get("prior_sessions_fixture_path")
    if prior_sessions_fixture:
        copy_session_fixture(ROOT / prior_sessions_fixture, sessions_dir)

    return {
        "business_dir": rel_path(business_dir),
        "snapshot": rel_path(snapshot_path),
        "sessions_dir": rel_path(sessions_dir),
    }


def render_acting_prompt(case: dict[str, Any], business_dir: Path) -> str:
    visible_case = {key: value for key, value in case.items() if key not in PROMPT_HIDDEN_FIELDS and not key.startswith("_")}
    return "\n".join(
        [
            "# Source-Need Generation Acting Prompt",
            "",
            "You are the acting agent for a Money Model Advisor source-need generation eval case.",
            "",
            "Use the money-model-advisor skill and local CLI as needed. Expected labels are intentionally hidden.",
            "",
            "Task: decide whether Money Models source-material search is needed for the current turn. If search is needed, generate a structured source need with `intent`, `layers`, and `focus_terms`. If search is not needed, set source need to null.",
            "",
            "Do not use source-material search as a substitute for missing business facts. If the current turn asks for a business recommendation that depends on missing economics, offer-stack facts, prior-session context, or deterministic math before an answer can be responsibly given, choose no source search for this step.",
            "",
            "Do use source-material search when the snapshot or prior-session context already contains enough facts for a source-backed explanation, diagnosis, comparison, or recommendation. A missing optional field should not block search when the user is asking for conceptual source support.",
            "",
            "Do not search for simple vocabulary answers that can be answered directly without citation. Source search is for source-backed advisory claims, not every definition.",
            "",
            "Keep layers minimal. Include only the corpus layers needed to support the source-backed claim; extra layers reduce precision.",
            "",
            "Choose intent by retrieval job, not by the mood of the final answer:",
            "",
            "- `teaching_evidence`: explain a Money Models concept or framework.",
            "- `diagnostic_evidence`: support interpretation of known business economics or constraints.",
            "- `comparison_evidence`: compare two concepts, options, or layers.",
            "- `recommendation_evidence`: source support for a concrete next move after enough business facts are known.",
            "",
            "Choose layers by the mechanism the source material must support:",
            "",
            "- front-end attraction offer -> `offers`",
            "- post-sale add-on or premium next offer -> `upsells`",
            "- payment plan, pay-less-now option, or friction-reducing alternative -> `downsells`",
            "- recurring maintenance, membership, or repeat post-purchase service -> `continuity`",
            "- CAC, gross profit, payback, or acquisition capacity interpretation -> `unit-economics`",
            "",
            "Use payback or CAC as focus terms without adding `unit-economics` when the source claim is about a concrete fix mechanism such as continuity or upsells.",
            "",
            "Allowed intents:",
            "",
            "- `teaching_evidence`",
            "- `diagnostic_evidence`",
            "- `comparison_evidence`",
            "- `recommendation_evidence`",
            "",
            "Allowed layers:",
            "",
            "- `unit-economics`",
            "- `offers`",
            "- `upsells`",
            "- `downsells`",
            "- `continuity`",
            "",
            f"Business dir: `{business_dir}`",
            "",
            "Visible case context:",
            "",
            "```json",
            json.dumps(visible_case, indent=2, sort_keys=True),
            "```",
            "",
            "After acting, complete the trace with `scripts/capture_source_need_trace.py complete ...`. Do not look up expected labels.",
            "",
        ]
    )


def read_json_value(value: str | None) -> Any:
    if value is None:
        return None
    candidate = Path(value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(value)


def prepare(args: argparse.Namespace) -> int:
    case = find_case(args.cases, args.case_id)
    run_dir = args.runs_dir / args.phase / args.case_id
    if run_dir.exists() and not args.force:
        raise SystemExit(f"run directory already exists; pass --force to replace: {run_dir}")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    business_dir = run_dir / "business"
    paths = prepare_business_dir(case, business_dir)
    prompt = render_acting_prompt(case, business_dir)
    (run_dir / "acting_prompt.md").write_text(prompt, encoding="utf-8")
    write_json(
        run_dir / "run_draft.json",
        {
            "case_id": case["case_id"],
            "created_at": utc_now(),
            "paths": paths,
            "visible_context": {key: value for key, value in case.items() if key not in PROMPT_HIDDEN_FIELDS and not key.startswith("_")},
        },
    )
    print(json.dumps({"run_dir": rel_path(run_dir), "acting_prompt": rel_path(run_dir / "acting_prompt.md")}, indent=2))
    return 0


def complete(args: argparse.Namespace) -> int:
    run_dir = args.run_dir
    draft_path = run_dir / "run_draft.json"
    if not draft_path.exists():
        raise SystemExit(f"missing run_draft.json: {draft_path}")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    source_need = read_json_value(args.source_need)
    source_search_decision = args.source_search_decision.lower() == "true"
    if not source_search_decision:
        source_need = None

    payload = {
        **draft,
        "completed_at": utc_now(),
        "source_search_decision": source_search_decision,
        "source_need": source_need,
        "notes": args.notes,
    }
    write_json(run_dir / RUN_FILE, payload)
    print(json.dumps({"run": rel_path(run_dir / RUN_FILE)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_source_need_cases.jsonl")
    prepare_parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "source_need")
    prepare_parser.add_argument("--phase", default="pilot")
    prepare_parser.add_argument("--force", action="store_true")
    prepare_parser.set_defaults(func=prepare)

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("run_dir", type=Path)
    complete_parser.add_argument("--source-search-decision", required=True, choices=("true", "false"))
    complete_parser.add_argument("--source-need", help="JSON object or path to JSON file. Omit when source search decision is false.")
    complete_parser.add_argument("--notes")
    complete_parser.set_defaults(func=complete)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
