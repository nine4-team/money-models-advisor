#!/usr/bin/env python3
"""Prepare and complete next-action classification trace artifacts.

This is a strict trace recorder, not a planner. `prepare` sets up an isolated
business directory and an acting prompt that excludes expected labels. `complete`
turns recorded workflow evidence into `run.json`. It never chooses the advisor's
next action from the case label.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR_NAME = ".money-model-advisor"
SNAPSHOT_FILE = "business_snapshot.json"
SESSIONS_DIR = "sessions"
DRAFT_FILE = "run_draft.json"
RUN_FILE = "run.json"

ACTION_TAXONOMY = {
    "clarify",
    "update_snapshot",
    "read_snapshot",
    "read_logs",
    "inspect_local_docs",
    "calculate",
    "diagnose",
    "search_source_material",
    "compose_answer_from_state",
    "answer_without_tool",
}

CONFIDENCE_VALUES = {"direct", "inferred", "missing"}

TOOL_LIKE_ACTIONS = {
    "update_snapshot",
    "read_snapshot",
    "read_logs",
    "inspect_local_docs",
    "calculate",
    "diagnose",
    "search_source_material",
}

PROMPT_HIDDEN_FIELDS = {
    "split",
    "turn_type",
    "snapshot_fixture_path",
    "local_docs_fixture_path",
    "prior_sessions_fixture_path",
    "required_actions",
    "allowed_actions",
    "forbidden_actions",
    "expected_first_action",
    "search_allowed",
    "expected_mutation",
    "label_rationale",
    "ambiguity",
    "severity_if_wrong",
}

FORBIDDEN_RUN_FIELDS = {
    "required_actions",
    "allowed_actions",
    "forbidden_actions",
    "expected_first_action",
    "search_allowed",
    "expected_mutation",
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


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def read_json_arg(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    candidate = Path(value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_tree_contents(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def prepare_business_dir(case: dict[str, Any], business_dir: Path) -> dict[str, str | None]:
    state_dir = business_dir / STATE_DIR_NAME
    sessions_dir = state_dir / SESSIONS_DIR
    snapshot_path = state_dir / SNAPSHOT_FILE

    business_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir.mkdir(parents=True, exist_ok=True)

    snapshot_fixture = ROOT / case["snapshot_fixture_path"]
    shutil.copy2(snapshot_fixture, snapshot_path)

    local_docs_fixture = case.get("local_docs_fixture_path")
    if local_docs_fixture:
        source = ROOT / local_docs_fixture
        if source.is_dir():
            copy_tree_contents(source, business_dir)
        else:
            shutil.copy2(source, business_dir / source.name)

    prior_sessions_fixture = case.get("prior_sessions_fixture_path")
    if prior_sessions_fixture:
        copy_session_fixture(ROOT / prior_sessions_fixture, sessions_dir)

    return {
        "business_dir": rel_path(business_dir),
        "state_dir": rel_path(state_dir),
        "snapshot": rel_path(snapshot_path),
        "sessions_dir": rel_path(sessions_dir),
    }


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


def render_acting_prompt(case: dict[str, Any], business_dir: Path) -> str:
    visible_case = {key: value for key, value in case.items() if key not in PROMPT_HIDDEN_FIELDS and not key.startswith("_")}
    return "\n".join(
        [
            "# Next-Action Eval Acting Prompt",
            "",
            "You are the acting agent for a Money Model Advisor next-action eval case.",
            "",
            "Use the money-model-advisor skill and local CLI. Choose the next action naturally from the case context. Do not ask for expected labels; they are intentionally hidden.",
            "",
            f"Business dir: `{business_dir}`",
            "",
            "Allowed CLI surface:",
            "",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot --business-dir <business_dir>`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli snapshot set --business-dir <business_dir> ...`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli logs --business-dir <business_dir> --full`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli calculate ...`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli diagnose --snapshot ...`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli search --business-dir <business_dir> --source-need-json ...`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli search \"raw debug query\" --layer <layer>`",
            "- `PYTHONPATH=src python3 -m money_model_architect.cli turn record --business-dir <business_dir> --user-message ... --assistant-message ...`",
            "",
            "Visible case context:",
            "",
            "```json",
            json.dumps(visible_case, indent=2, sort_keys=True),
            "```",
            "",
            "After acting, record observable steps for `complete`. Do not infer actions from the hidden label.",
            "",
        ]
    )


def prepare(args: argparse.Namespace) -> int:
    case = find_case(args.cases, args.case_id)
    run_dir = args.runs_dir / args.phase / args.case_id
    if run_dir.exists() and not args.force:
        raise SystemExit(f"run directory already exists; pass --force to replace: {run_dir}")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    business_dir = run_dir / "business_dir"
    stdout_dir = run_dir / "stdout"
    stderr_dir = run_dir / "stderr"
    stdout_dir.mkdir(parents=True, exist_ok=True)
    stderr_dir.mkdir(parents=True, exist_ok=True)
    paths = prepare_business_dir(case, business_dir)

    snapshot_path = business_dir / STATE_DIR_NAME / SNAPSHOT_FILE
    prompt_path = run_dir / "acting_prompt.md"
    prompt_path.write_text(render_acting_prompt(case, business_dir.resolve()), encoding="utf-8")

    draft = {
        "case_id": case["case_id"],
        "split": case["split"],
        "phase": args.phase,
        "created_at": utc_now(),
        "status": "prepared",
        "business_dir": rel_path(business_dir),
        "paths": paths,
        "fixtures": {
            "snapshot_fixture_path": case["snapshot_fixture_path"],
            "local_docs_fixture_path": case.get("local_docs_fixture_path"),
            "prior_sessions_fixture_path": case.get("prior_sessions_fixture_path"),
        },
        "snapshot_hash": {
            "start": sha256_file(snapshot_path),
            "end": None,
        },
        "acting_prompt_path": rel_path(prompt_path),
        "workflow_steps": [],
        "session_paths": [],
        "actual_actions": [],
        "final_answer_path": None,
    }
    write_json(run_dir / DRAFT_FILE, draft)
    print(json.dumps({"run_dir": rel_path(run_dir), "draft": rel_path(run_dir / DRAFT_FILE), "acting_prompt": rel_path(prompt_path)}, indent=2))
    return 0


def complete(args: argparse.Namespace) -> int:
    run_dir = args.run_dir
    draft_path = run_dir / DRAFT_FILE
    if not draft_path.exists():
        raise SystemExit(f"missing draft: {draft_path}")

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    final_answer_path = None
    if args.final_answer:
        final_answer_path = run_dir / "final_answer.txt"
        final_answer_path.write_text(args.final_answer, encoding="utf-8")
    elif args.final_answer_file:
        source = args.final_answer_file
        final_answer_path = run_dir / "final_answer.txt"
        shutil.copy2(source, final_answer_path)

    workflow_steps = read_json_arg(args.workflow_steps, draft.get("workflow_steps", []))
    session_paths = read_json_arg(args.session_paths, draft.get("session_paths", []))
    actual_actions = read_json_arg(args.actual_actions, draft.get("actual_actions", []))

    snapshot_path = ROOT / draft["paths"]["snapshot"]
    run = {
        **draft,
        "completed_at": utc_now(),
        "status": "completed",
        "workflow_steps": workflow_steps,
        "session_paths": session_paths,
        "actual_actions": actual_actions,
        "final_answer_path": rel_path(final_answer_path) if final_answer_path else draft.get("final_answer_path"),
        "snapshot_hash": {
            "start": draft["snapshot_hash"]["start"],
            "end": sha256_file(snapshot_path),
        },
    }

    errors = validate_run(run, run_dir)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        return 1

    run.pop("status", None)
    write_json(run_dir / RUN_FILE, run)
    print(json.dumps({"valid": True, "run": rel_path(run_dir / RUN_FILE)}, indent=2))
    return 0


def validate(args: argparse.Namespace) -> int:
    run_path = args.run if args.run.is_file() else args.run / RUN_FILE
    if not run_path.exists():
        raise SystemExit(f"run not found: {run_path}")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    errors = validate_run(run, run_path.parent)
    print(json.dumps({"valid": not errors, "errors": errors, "run": rel_path(run_path)}, indent=2))
    return 1 if errors else 0


def validate_run(run: dict[str, Any], run_dir: Path) -> list[str]:
    errors: list[str] = []
    for field in ("case_id", "split", "phase", "business_dir", "fixtures", "snapshot_hash", "workflow_steps", "session_paths", "actual_actions"):
        if field not in run:
            errors.append(f"missing field: {field}")

    if any(field in run for field in FORBIDDEN_RUN_FIELDS):
        errors.append("run artifact must not contain expected-label fields")

    workflow_steps = run.get("workflow_steps", [])
    if not isinstance(workflow_steps, list):
        errors.append("workflow_steps must be a list")
        workflow_steps = []
    for index, step in enumerate(workflow_steps):
        if not isinstance(step, dict):
            errors.append(f"workflow_steps[{index}] must be an object")
            continue
        for field in ("index", "kind"):
            if field not in step:
                errors.append(f"workflow_steps[{index}] missing {field}")
        if step.get("kind") == "cli_command":
            for field in ("command", "exit_code"):
                if field not in step:
                    errors.append(f"workflow_steps[{index}] cli_command missing {field}")

    actual_actions = run.get("actual_actions", [])
    if not isinstance(actual_actions, list):
        errors.append("actual_actions must be a list")
        actual_actions = []
    if not actual_actions:
        errors.append("actual_actions must contain at least one action before writing run.json")
    for index, item in enumerate(actual_actions):
        if not isinstance(item, dict):
            errors.append(f"actual_actions[{index}] must be an object")
            continue
        action = item.get("action")
        confidence = item.get("confidence")
        if action not in ACTION_TAXONOMY:
            errors.append(f"actual_actions[{index}] unknown action: {action}")
        if confidence not in CONFIDENCE_VALUES:
            errors.append(f"actual_actions[{index}] unknown confidence: {confidence}")
        if item.get("index") != index:
            errors.append(f"actual_actions[{index}] index must equal {index}")
        if confidence == "direct" and action in TOOL_LIKE_ACTIONS:
            if not item.get("evidence_type"):
                errors.append(f"actual_actions[{index}] direct tool-like action missing evidence_type")
            if not item.get("evidence_ref"):
                errors.append(f"actual_actions[{index}] direct tool-like action missing evidence_ref")
        if confidence == "missing" and not item.get("evidence_note"):
            errors.append(f"actual_actions[{index}] missing-confidence action needs evidence_note")

    prompt_path = run.get("acting_prompt_path")
    if prompt_path:
        full_prompt_path = ROOT / prompt_path
        if full_prompt_path.exists():
            prompt = full_prompt_path.read_text(encoding="utf-8")
            leaked = [field for field in PROMPT_HIDDEN_FIELDS if field in prompt]
            if leaked:
                errors.append(f"acting prompt leaks expected-label fields: {', '.join(sorted(leaked))}")

    final_answer_path = run.get("final_answer_path")
    if final_answer_path and not (ROOT / final_answer_path).exists():
        errors.append(f"final_answer_path does not exist: {final_answer_path}")

    business_dir = run.get("business_dir")
    if business_dir and not (ROOT / business_dir).exists():
        errors.append(f"business_dir does not exist: {business_dir}")

    if run_dir.name != run.get("case_id") and run_dir.parent.name != run.get("case_id"):
        # Allow validating a copied run file, but flag obviously mismatched generated dirs.
        if "evals/runs/next_action" in rel_path(run_dir):
            errors.append("run directory does not match case_id")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Prepare an isolated eval case directory")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("--phase", default="baseline")
    prepare_parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "advisor_tool_use_cases.jsonl")
    prepare_parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "next_action")
    prepare_parser.add_argument("--force", action="store_true")
    prepare_parser.set_defaults(func=prepare)

    complete_parser = subparsers.add_parser("complete", help="Complete a prepared trace and write run.json")
    complete_parser.add_argument("run_dir", type=Path)
    complete_parser.add_argument("--workflow-steps", help="JSON array or path to JSON array")
    complete_parser.add_argument("--session-paths", help="JSON array or path to JSON array")
    complete_parser.add_argument("--actual-actions", help="JSON array or path to JSON array")
    complete_parser.add_argument("--final-answer")
    complete_parser.add_argument("--final-answer-file", type=Path)
    complete_parser.set_defaults(func=complete)

    validate_parser = subparsers.add_parser("validate", help="Validate a run.json or run directory")
    validate_parser.add_argument("run", type=Path)
    validate_parser.set_defaults(func=validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
