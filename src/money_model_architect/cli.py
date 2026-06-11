"""Command-line entry point for the local proof harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .advisor_queries import SourceNeed, build_advisor_queries
from .advisor_retrieval import execute_advisor_queries
from .business_context import advisor_paths, ensure_advisor_state, utc_now
from .calculator import (
    UnitEconomics,
    cac,
    cfa_level,
    gross_margin,
    gross_profit,
    lifetime_gross_profit,
    payback_period_months,
)
from .diagnose import diagnose
from .retrieval import CorpusIndex
from .setup_intake import load_answers, run_setup
from .snapshot import BusinessSnapshot

LAYERS = ("unit-economics", "offers", "upsells", "downsells", "continuity")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Money Model Architect local proof harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    source_material = subparsers.add_parser("search", help="Get citation-ready Money Models source chunks")
    source_material.add_argument("query", nargs="?", help="Raw debug/manual search query")
    source_material.add_argument("--business-dir", help="Directory containing advisor state for source-need search")
    source_material.add_argument("--source-need-json", help="JSON object or path to JSON file with agent-selected SourceNeed")
    source_material.add_argument("--layer", choices=LAYERS)
    source_material.add_argument("--top-k", type=int, default=5)

    calc = subparsers.add_parser("calculate", help="Run deterministic unit-economics formulas")
    calc.add_argument("metric", choices=("cac", "gross-profit", "gross-margin", "ltgp", "payback", "cfa-level"))
    calc.add_argument("--inputs", required=True, help="JSON object with metric inputs")

    diag = subparsers.add_parser("diagnose", help="Diagnose the active money-model constraint")
    diag.add_argument("--snapshot", required=True, help="JSON business snapshot")

    setup = subparsers.add_parser("setup", help="Initialize advisor state for a business directory")
    setup.add_argument("--business-dir", required=True, help="Directory for local business context and advisor state")
    setup.add_argument("--answers", help="JSON object or path to JSON file with setup answers")
    setup.add_argument("--interactive", action="store_true", help="Prompt for missing setup fields")

    snapshot = subparsers.add_parser("snapshot", help="Show or update the saved BusinessSnapshot")
    snapshot.add_argument("snapshot_action", nargs="?", choices=("set",), help="Use 'set' to update snapshot fields")
    snapshot.add_argument("assignments", nargs="*", help="Field assignments such as economics.cac=350")
    snapshot.add_argument("--business-dir", required=True, help="Directory containing advisor state")

    logs = subparsers.add_parser("logs", help="Show saved advisor session logs")
    logs.add_argument("--business-dir", required=True, help="Directory containing advisor state")
    logs.add_argument("--limit", type=int, default=10, help="Maximum session turns to return")
    logs.add_argument("--full", action="store_true", help="Return full saved session records")

    turn = subparsers.add_parser("turn", help="Record completed agent-operated advisor turns")
    turn_subparsers = turn.add_subparsers(dest="turn_command", required=True)
    record = turn_subparsers.add_parser("record", help="Persist one completed advisor turn")
    record.add_argument("--business-dir", required=True, help="Directory containing advisor state")
    record.add_argument("--user-message", required=True)
    record.add_argument("--assistant-message", required=True)
    record.add_argument("--actions-json", default="[]", help="JSON array or path to JSON file")
    record.add_argument("--source-events-json", default="[]", help="JSON array or path to JSON file")
    record.add_argument("--cited-chunk-ids-json", default="[]", help="JSON array or path to JSON file")
    record.add_argument("--metadata-json", default="{}", help="JSON object or path to JSON file")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "search":
        if args.source_need_json:
            if not args.business_dir:
                parser.error("search --source-need-json requires --business-dir")
            paths = advisor_paths(Path(args.business_dir))
            ensure_advisor_state(paths)
            snapshot = BusinessSnapshot.load(paths.snapshot)
            source_need = _parse_source_need(_read_json_value(args.source_need_json))
            queries = build_advisor_queries(snapshot, source_need)
            evidence = execute_advisor_queries(
                queries,
                _repo_root() / "corpus" / "transcripts",
                top_k=args.top_k,
            )
            payload = {
                "business_dir": str(paths.business_dir),
                "source_need": _source_need_to_dict(source_need),
                "queries": [query.to_dict() for query in queries],
                "source_material": [item.to_dict() for item in evidence],
            }
            print(json.dumps(payload, indent=2))
            return 0

        if not args.query:
            parser.error("search requires a raw query or --source-need-json")
        index = CorpusIndex.from_transcripts(_repo_root() / "corpus" / "transcripts")
        results = index.search(args.query, layer=args.layer, top_k=args.top_k)
        payload = {
            "query": args.query,
            "layer": args.layer,
            "top_k": args.top_k,
            "source_material": [
                {
                    "id": result.chunk.id,
                    "chapter": result.chunk.chapter,
                    "layer": result.chunk.layer,
                    "layers": list(result.chunk.layers),
                    "score": round(result.score, 3),
                    "char_start": result.chunk.char_start,
                    "char_end": result.chunk.char_end,
                    "text": result.chunk.text,
                }
                for result in results
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "calculate":
        inputs = json.loads(args.inputs)
        metric = args.metric
        if metric == "cac":
            value = cac(inputs["total_acquisition_cost"], inputs["new_customers"])
        elif metric == "gross-profit":
            value = gross_profit(inputs["price"], inputs["cogs"])
        elif metric == "gross-margin":
            value = gross_margin(inputs["price"], inputs["cogs"])
        elif metric == "ltgp":
            value = lifetime_gross_profit(inputs["monthly_price"], inputs["monthly_churn_rate"], inputs["gross_margin"])
        elif metric == "payback":
            value = payback_period_months(inputs["cac"], inputs["month_one_gp"], inputs["monthly_recurring_gp"])
        else:
            value = cfa_level(inputs["cac"], inputs["first_30_day_gp"])
        print(json.dumps({"metric": metric, "value": value}, indent=2))
        return 0

    if args.command == "setup":
        answers = load_answers(args.answers) if getattr(args, "answers", None) else None
        snapshot, summary = run_setup(
            Path(args.business_dir),
            answers=answers,
            interactive=getattr(args, "interactive", False),
        )
        paths = advisor_paths(Path(args.business_dir))
        payload = {
            "business_dir": str(paths.business_dir),
            "state_dir": str(paths.state_dir),
            "snapshot": str(paths.snapshot),
            "summary": summary,
            "advisory_status": snapshot.advisor_state.advisory_status,
            "ready_for_payback_diagnosis": snapshot.advisor_state.ready_for_payback_diagnosis,
            "ready_for_offer_stack_diagnosis": snapshot.advisor_state.ready_for_offer_stack_diagnosis,
            "missing_fields": snapshot.advisor_state.missing_fields,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "snapshot":
        paths = advisor_paths(Path(args.business_dir))
        ensure_advisor_state(paths)
        snapshot = BusinessSnapshot.load(paths.snapshot)
        if args.snapshot_action == "set":
            if not args.assignments:
                parser.error("snapshot set requires at least one field=value assignment")
            updates = []
            for assignment in args.assignments:
                field_name, value = _parse_assignment(assignment)
                _set_snapshot_field(snapshot, field_name, value)
                snapshot.field_sources[field_name] = {
                    "source_type": "cli",
                    "confidence": "high",
                    "updated_at": utc_now(),
                }
                updates.append({"field": field_name, "value": value})
            snapshot.save(paths.snapshot)
            print(json.dumps({"snapshot": str(paths.snapshot), "updated": updates, "state": snapshot.to_dict()}, indent=2))
            return 0

        print(json.dumps(snapshot.to_dict(), indent=2))
        return 0

    if args.command == "logs":
        paths = advisor_paths(Path(args.business_dir))
        ensure_advisor_state(paths)
        records = []
        for path in sorted(paths.sessions_dir.glob("*.json"), reverse=True)[: args.limit]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if args.full:
                payload = {"path": str(path), **payload}
            else:
                payload = _summarize_log(path, payload)
            records.append(payload)
        print(json.dumps({"business_dir": str(paths.business_dir), "logs": records}, indent=2))
        return 0

    if args.command == "turn" and args.turn_command == "record":
        paths = advisor_paths(Path(args.business_dir))
        ensure_advisor_state(paths)
        snapshot = BusinessSnapshot.load(paths.snapshot)
        actions = _expect_json_type(_read_json_value(args.actions_json), list, "actions-json")
        source_events = _expect_json_type(_read_json_value(args.source_events_json), list, "source-events-json")
        cited_chunk_ids = _expect_json_type(_read_json_value(args.cited_chunk_ids_json), list, "cited-chunk-ids-json")
        metadata = _expect_json_type(_read_json_value(args.metadata_json), dict, "metadata-json")
        created_at = utc_now()
        session_path = _write_turn_record(
            paths.sessions_dir,
            {
                "created_at": created_at,
                "user_message": args.user_message,
                "assistant_message": args.assistant_message,
                "actions": actions,
                "source_events": source_events,
                "cited_chunk_ids": cited_chunk_ids,
                "metadata": metadata,
                "snapshot": snapshot.to_dict(),
            },
        )
        print(
            json.dumps(
                {
                    "recorded": True,
                    "session_path": str(session_path),
                    "created_at": created_at,
                    "source_event_count": len(source_events),
                    "cited_chunk_ids": cited_chunk_ids,
                },
                indent=2,
            )
        )
        return 0

    snapshot = json.loads(args.snapshot)
    economics = UnitEconomics(
        cac=snapshot["cac"],
        first_30_day_gross_profit=snapshot.get("first_30_day_gross_profit", 0.0),
        monthly_recurring_gross_profit=snapshot.get("monthly_recurring_gross_profit", 0.0),
        lifetime_gross_profit=snapshot.get("lifetime_gross_profit"),
        gross_margin=snapshot.get("gross_margin"),
        service_business=snapshot.get("service_business", False),
    )
    print(json.dumps(diagnose(economics).to_dict(), indent=2))
    return 0


def _parse_assignment(assignment: str) -> tuple[str, Any]:
    if "=" not in assignment:
        raise SystemExit(f"invalid assignment {assignment!r}; expected field=value")
    field_name, raw_value = assignment.split("=", 1)
    field_name = field_name.strip()
    if not field_name:
        raise SystemExit(f"invalid assignment {assignment!r}; field name is empty")
    return field_name, _parse_value(raw_value.strip())


def _parse_value(raw_value: str) -> Any:
    lower = raw_value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"none", "null"}:
        return None
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _read_json_value(value: str) -> Any:
    stripped = value.strip()
    if stripped.startswith(("{", "[")):
        return json.loads(stripped)
    candidate = Path(value).expanduser()
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(stripped)


def _expect_json_type(value: Any, expected_type: type, label: str) -> Any:
    if not isinstance(value, expected_type):
        raise SystemExit(f"{label} must decode to {expected_type.__name__}")
    return value


def _parse_source_need(value: Any) -> SourceNeed:
    if not isinstance(value, dict):
        raise SystemExit("source-need-json must decode to an object")
    intent = value.get("intent")
    layers = value.get("layers", [])
    focus_terms = value.get("focus_terms", [])
    user_turn = value.get("user_turn", "")
    if not isinstance(intent, str) or not intent:
        raise SystemExit("source need requires non-empty string field: intent")
    if not isinstance(layers, list) or not all(isinstance(layer, str) for layer in layers):
        raise SystemExit("source need field layers must be a list of strings")
    if not isinstance(focus_terms, list) or not all(isinstance(term, str) for term in focus_terms):
        raise SystemExit("source need field focus_terms must be a list of strings")
    if not isinstance(user_turn, str):
        raise SystemExit("source need field user_turn must be a string when supplied")
    invalid_layers = [layer for layer in layers if layer not in LAYERS]
    if invalid_layers:
        raise SystemExit(f"unknown source need layer(s): {', '.join(invalid_layers)}")
    return SourceNeed(intent=intent, layers=tuple(layers), focus_terms=tuple(focus_terms), user_turn=user_turn)


def _source_need_to_dict(source_need: SourceNeed) -> dict[str, Any]:
    return {
        "intent": source_need.intent,
        "layers": list(source_need.layers),
        "focus_terms": list(source_need.focus_terms),
        "user_turn": source_need.user_turn,
    }


def _write_turn_record(sessions_dir: Path, payload: dict[str, Any]) -> Path:
    timestamp = payload["created_at"].replace(":", "").replace("-", "").replace("Z", "")
    existing = len(list(sessions_dir.glob(f"{timestamp}*.json")))
    suffix = f"_{existing + 1:02d}" if existing else ""
    path = sessions_dir / f"{timestamp}{suffix}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _set_snapshot_field(snapshot: BusinessSnapshot, field_name: str, value: Any) -> None:
    target: Any = snapshot
    parts = field_name.split(".")
    for part in parts[:-1]:
        if not hasattr(target, part):
            raise SystemExit(f"unknown snapshot field path: {field_name}")
        target = getattr(target, part)
    final = parts[-1]
    if not hasattr(target, final):
        raise SystemExit(f"unknown snapshot field path: {field_name}")
    setattr(target, final, value)
    snapshot.refresh()


def _summarize_log(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("evidence", [])
    source_events = payload.get("source_events", [])
    source_ids = []
    for item in evidence:
        for chunk in item.get("chunks", []):
            chunk_id = chunk.get("id")
            if chunk_id and chunk_id not in source_ids:
                source_ids.append(chunk_id)
    for chunk_id in payload.get("cited_chunk_ids", []):
        if chunk_id and chunk_id not in source_ids:
            source_ids.append(chunk_id)
    for item in source_events:
        for chunk in item.get("chunks", []):
            chunk_id = chunk.get("id")
            if chunk_id and chunk_id not in source_ids:
                source_ids.append(chunk_id)
    return {
        "path": str(path),
        "created_at": payload.get("created_at"),
        "user_message": payload.get("user_message"),
        "assistant_message": payload.get("assistant_message"),
        "actions": payload.get("actions", []),
        "retrieval_queries": payload.get("retrieval_queries", []),
        "source_events": source_events,
        "source_chunk_ids": source_ids,
    }


if __name__ == "__main__":
    raise SystemExit(main())
