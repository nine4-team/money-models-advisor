"""Command-line entry point for the local proof harness."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .advisor_queries import SourceNeed, build_advisor_queries
from .advisor_retrieval import RETRIEVAL_BACKENDS, VECTOR_STORES, execute_advisor_queries
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
from .embeddings import OpenAIEmbeddingClient
from .retrieval import CorpusIndex
from .setup_intake import load_answers, run_setup
from .snapshot import BusinessSnapshot
from .vector_store import PineconeVectorStore, VectorStoreError

LAYERS = ("unit-economics", "offers", "upsells", "downsells", "continuity")
ACTION_LABELS = {
    "setup_state",
    "session_start",
    "read_snapshot",
    "update_snapshot",
    "calculate",
    "diagnose",
    "search_source_material",
    "logs",
    "answer",
    "turn_record",
    "session_finish",
    "inspect_local_docs",
    "clarify",
}
SOURCE_NEED_INTENTS = {
    "teaching_evidence",
    "diagnostic_evidence",
    "comparison_evidence",
    "recommendation_evidence",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _reject_repo_business_dir(business_dir: Path) -> None:
    if os.getenv("MMA_ALLOW_REPO_BUSINESS_DIR") == "1":
        return
    if business_dir.resolve() == _repo_root().resolve():
        raise SystemExit(
            "Refusing to use the advisor repo as --business-dir. "
            "Pass the business/context directory instead, or set MMA_ALLOW_REPO_BUSINESS_DIR=1 for an intentional dev run."
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Money Model Architect local proof harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    source_material = subparsers.add_parser("search", help="Get citation-ready Money Models source chunks")
    source_material.add_argument("query", nargs="?", help="Raw debug/manual search query")
    source_material.add_argument("--business-dir", help="Directory containing advisor state for source-need search")
    source_material.add_argument("--source-need-json", help="JSON object or path to JSON file with agent-selected SourceNeed")
    source_material.add_argument("--layer", choices=LAYERS)
    source_material.add_argument("--top-k", type=int, default=5)
    source_material.add_argument("--backend", choices=RETRIEVAL_BACKENDS, default="bm25")
    source_material.add_argument("--vector-store", choices=VECTOR_STORES, default="local")

    index_cmd = subparsers.add_parser("index", help="Manage hosted retrieval indexes")
    index_subparsers = index_cmd.add_subparsers(dest="index_command", required=True)
    pinecone = index_subparsers.add_parser("pinecone", help="Upsert corpus chunks to Pinecone")
    pinecone.add_argument("--namespace", help="Pinecone namespace; defaults to MMA_PINECONE_NAMESPACE or money-models")
    pinecone.add_argument("--batch-size", type=int, default=64)

    calc = subparsers.add_parser("calculate", help="Run deterministic unit-economics formulas")
    calc.add_argument("metric", choices=("cac", "gross-profit", "gross-margin", "ltgp", "payback", "cfa-level"))
    calc.add_argument("--inputs", required=True, help="JSON object with metric inputs")

    diag = subparsers.add_parser("diagnose", help="Diagnose the active money-model constraint")
    diag.add_argument("--business-dir", help="Directory containing advisor state")
    diag.add_argument("--snapshot", help="JSON object or path to JSON file with economics or BusinessSnapshot data")

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

    session = subparsers.add_parser("session", help="Prepare an agent-operated advisor session")
    session_subparsers = session.add_subparsers(dest="session_command", required=True)
    session_start = session_subparsers.add_parser("start", help="Load advisor state and recent traces for one agent turn")
    session_start.add_argument("--business-dir", required=True, help="Directory containing advisor state")
    session_start.add_argument("--user-message", help="Current human message for trace context")
    session_start.add_argument("--limit", type=int, default=3, help="Recent turn summaries to include")
    session_finish = session_subparsers.add_parser("finish", help="Validate and persist one completed advisor turn")
    session_finish.add_argument("--business-dir", required=True, help="Directory containing advisor state")
    session_finish.add_argument("--record-json", required=True, help="JSON object or path to a completed turn record")

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
                retrieval_backend=args.backend,
                vector_store=args.vector_store,
            )
            payload = {
                "business_dir": str(paths.business_dir),
                "retrieval_backend": args.backend,
                "vector_store": args.vector_store,
                "source_need": _source_need_to_dict(source_need),
                "queries": [query.to_dict() for query in queries],
                "source_material": [item.to_dict() for item in evidence],
            }
            print(json.dumps(payload, indent=2))
            return 0

        if not args.query:
            parser.error("search requires a raw query or --source-need-json")
        index = CorpusIndex.from_transcripts(_repo_root() / "corpus" / "transcripts")
        results = _search_index(index, args.query, layer=args.layer, top_k=args.top_k, backend=args.backend, vector_store=args.vector_store)
        payload = {
            "query": args.query,
            "layer": args.layer,
            "top_k": args.top_k,
            "retrieval_backend": args.backend,
            "vector_store": args.vector_store,
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

    if args.command == "index" and args.index_command == "pinecone":
        index = CorpusIndex.from_transcripts(_repo_root() / "corpus" / "transcripts")
        embedding_client = OpenAIEmbeddingClient()
        records = index.vector_records(embedding_client)
        store = PineconeVectorStore.from_env()
        upserted = 0
        try:
            for start in range(0, len(records), args.batch_size):
                upserted += store.upsert(records[start : start + args.batch_size], namespace=args.namespace)
        except VectorStoreError as exc:
            raise SystemExit(str(exc)) from exc
        payload = {
            "vector_store": "pinecone",
            "namespace": args.namespace or store.default_namespace,
            "chunks": len(index.chunks),
            "records_upserted": upserted,
            "embedding_model": embedding_client.model,
            "chunking_strategy": index.strategy.name,
            "embedding_cache": embedding_client.stats.to_dict(),
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

    if args.command == "session" and args.session_command == "start":
        paths = advisor_paths(Path(args.business_dir))
        _reject_repo_business_dir(paths.business_dir)
        ensure_advisor_state(paths)
        snapshot = BusinessSnapshot.load(paths.snapshot)
        payload = {
            "business_dir": str(paths.business_dir),
            "state_dir": str(paths.state_dir),
            "snapshot": str(paths.snapshot),
            "sessions_dir": str(paths.sessions_dir),
            "user_message": args.user_message,
            "advisor_state": _advisor_state_summary(snapshot),
            "recent_turns": _recent_turn_summaries(paths.sessions_dir, args.limit),
            "available_operations": [
                "read_snapshot",
                "update_snapshot",
                "calculate",
                "search_source_material",
                "logs",
                "turn_record",
                "session_finish",
            ],
            "trace_requirements": [
                "Record the completed turn with session finish.",
                "Include every CLI-backed action in the record actions list.",
                "Include one source_events entry per source-material search.",
                "Include cited chunk ids when source material supports the answer.",
            ],
            "boundary": {
                "agent_owns": [
                    "advisory judgment",
                    "local document inspection",
                    "source-need generation",
                    "answer synthesis",
                ],
                "cli_owns": [
                    "snapshot persistence",
                    "deterministic calculations",
                    "source-material retrieval",
                    "trace recording",
                ],
            },
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "session" and args.session_command == "finish":
        paths = advisor_paths(Path(args.business_dir))
        _reject_repo_business_dir(paths.business_dir)
        ensure_advisor_state(paths)
        snapshot = BusinessSnapshot.load(paths.snapshot)
        record = _expect_json_type(_read_json_value(args.record_json), dict, "record-json")
        normalized, warnings = _normalize_session_finish_record(record)
        created_at = utc_now()
        session_path = _write_turn_record(
            paths.sessions_dir,
            {
                "created_at": created_at,
                "user_message": normalized["user_message"],
                "assistant_message": normalized["assistant_message"],
                "actions": normalized["actions"],
                "source_events": normalized["source_events"],
                "calculation_events": normalized["calculation_events"],
                "cited_chunk_ids": normalized["cited_chunk_ids"],
                "metadata": normalized["metadata"],
                "snapshot": snapshot.to_dict(),
            },
        )
        print(
            json.dumps(
                {
                    "recorded": True,
                    "session_path": str(session_path),
                    "created_at": created_at,
                    "warnings": warnings,
                    "source_event_count": len(normalized["source_events"]),
                    "calculation_event_count": len(normalized["calculation_events"]),
                    "cited_chunk_ids": normalized["cited_chunk_ids"],
                },
                indent=2,
            )
        )
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

    if args.business_dir:
        paths = advisor_paths(Path(args.business_dir))
        _reject_repo_business_dir(paths.business_dir)
        ensure_advisor_state(paths)
        snapshot_payload = BusinessSnapshot.load(paths.snapshot).to_dict()
    elif args.snapshot:
        snapshot_payload = _expect_json_type(_read_json_value(args.snapshot), dict, "snapshot")
    else:
        raise SystemExit("diagnose requires either --business-dir or --snapshot")
    economics = _unit_economics_from_snapshot_payload(snapshot_payload)
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


def _unit_economics_from_snapshot_payload(payload: dict[str, Any]) -> UnitEconomics:
    if isinstance(payload.get("economics"), dict):
        economics = payload["economics"]
        business = payload.get("business", {})
        money_model = payload.get("money_model", {})
        service_business = _snapshot_payload_looks_service_based(business, money_model)
    else:
        economics = payload
        service_business = bool(economics.get("service_business", False))

    cac_value = economics.get("cac")
    if cac_value is None:
        raise SystemExit("diagnose requires economics.cac")

    return UnitEconomics(
        cac=cac_value,
        first_30_day_gross_profit=economics.get("first_30_day_gross_profit") or 0.0,
        monthly_recurring_gross_profit=economics.get("monthly_recurring_gross_profit") or 0.0,
        lifetime_gross_profit=economics.get("lifetime_gross_profit"),
        gross_margin=economics.get("gross_margin"),
        service_business=service_business,
    )


def _snapshot_payload_looks_service_based(business: Any, money_model: Any) -> bool:
    text_parts: list[str] = []
    if isinstance(business, dict):
        for field_name in ("business_type", "delivery_model"):
            value = business.get(field_name)
            if isinstance(value, str):
                text_parts.append(value)
    if isinstance(money_model, dict):
        core_offer = money_model.get("core_offer", {})
        if isinstance(core_offer, dict):
            description = core_offer.get("description")
            if isinstance(description, str):
                text_parts.append(description)
    text = " ".join(text_parts).lower()
    return any(term in text for term in ("service", "services", "consulting", "agency", "design", "implementation"))


def _normalize_session_finish_record(record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    user_message = _required_string(record, "user_message")
    assistant_message = _required_string(record, "assistant_message")
    actions = _required_string_list(record, "actions")
    invalid_actions = [action for action in actions if action not in ACTION_LABELS]
    if invalid_actions:
        raise SystemExit(f"record-json actions contain unknown label(s): {', '.join(invalid_actions)}")

    source_events = record.get("source_events", [])
    if not isinstance(source_events, list):
        raise SystemExit("record-json source_events must be a list when supplied")
    normalized_events = [_normalize_source_event(event, index) for index, event in enumerate(source_events, start=1)]

    calculation_events = record.get("calculation_events", [])
    if not isinstance(calculation_events, list):
        raise SystemExit("record-json calculation_events must be a list when supplied")
    normalized_calculation_events = [
        _normalize_calculation_event(event, index) for index, event in enumerate(calculation_events, start=1)
    ]
    if "calculate" in actions and not normalized_calculation_events:
        raise SystemExit("record-json actions include calculate, so calculation_events must contain at least one event")

    cited_chunk_ids = record.get("cited_chunk_ids", [])
    if not isinstance(cited_chunk_ids, list) or not all(isinstance(chunk_id, str) for chunk_id in cited_chunk_ids):
        raise SystemExit("record-json cited_chunk_ids must be a list of strings when supplied")
    cited_chunk_ids = _dedupe_strings(cited_chunk_ids)

    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        raise SystemExit("record-json metadata must be an object when supplied")

    warnings = _session_finish_warnings(normalized_events, cited_chunk_ids, metadata)
    return (
        {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "actions": actions,
            "source_events": normalized_events,
            "calculation_events": normalized_calculation_events,
            "cited_chunk_ids": cited_chunk_ids,
            "metadata": metadata,
        },
        warnings,
    )


def _required_string(record: dict[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"record-json requires non-empty string field: {field_name}")
    return value


def _required_string_list(record: dict[str, Any], field_name: str) -> list[str]:
    value = record.get(field_name)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise SystemExit(f"record-json requires non-empty string list field: {field_name}")
    return value


def _normalize_source_event(event: Any, index: int) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise SystemExit(f"record-json source_events[{index}] must be an object")
    source_need = event.get("source_need")
    if not isinstance(source_need, dict):
        raise SystemExit(f"record-json source_events[{index}].source_need must be an object")
    _validate_source_need_payload(source_need, f"record-json source_events[{index}].source_need")

    queries = event.get("queries")
    if queries is None and isinstance(event.get("query"), str):
        queries = [event["query"]]
    if not isinstance(queries, list) or not queries or not all(isinstance(query, str) and query.strip() for query in queries):
        raise SystemExit(f"record-json source_events[{index}] requires non-empty queries list")
    _validate_query_variants_executed(source_need, queries, f"record-json source_events[{index}]")

    chunks = event.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise SystemExit(f"record-json source_events[{index}] requires non-empty chunks list")
    for chunk_index, chunk in enumerate(chunks, start=1):
        if not isinstance(chunk, dict):
            raise SystemExit(f"record-json source_events[{index}].chunks[{chunk_index}] must be an object")
        if not isinstance(chunk.get("id"), str) or not chunk["id"].strip():
            raise SystemExit(f"record-json source_events[{index}].chunks[{chunk_index}] requires non-empty id")

    normalized = dict(event)
    normalized["queries"] = queries
    normalized["query"] = queries[0]
    normalized["chunks"] = chunks
    return normalized


def _normalize_calculation_event(event: Any, index: int) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise SystemExit(f"record-json calculation_events[{index}] must be an object")
    metric = event.get("metric")
    valid_metrics = {"cac", "gross-profit", "gross-margin", "ltgp", "payback", "cfa-level"}
    if not isinstance(metric, str) or metric not in valid_metrics:
        raise SystemExit(
            f"record-json calculation_events[{index}].metric must be one of: {', '.join(sorted(valid_metrics))}"
        )
    inputs = event.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        raise SystemExit(f"record-json calculation_events[{index}].inputs must be a non-empty object")
    if not all(isinstance(key, str) and key.strip() for key in inputs):
        raise SystemExit(f"record-json calculation_events[{index}].inputs keys must be non-empty strings")
    value = event.get("value")
    if not isinstance(value, (int, float)):
        raise SystemExit(f"record-json calculation_events[{index}].value must be a number")
    normalized = dict(event)
    normalized["metric"] = metric
    normalized["inputs"] = inputs
    normalized["value"] = value
    return normalized


def _validate_source_need_payload(source_need: dict[str, Any], label: str) -> None:
    intent = source_need.get("intent")
    if intent not in SOURCE_NEED_INTENTS:
        raise SystemExit(f"{label}.intent must be one of: {', '.join(sorted(SOURCE_NEED_INTENTS))}")
    layers = source_need.get("layers")
    if not isinstance(layers, list) or not layers or not all(isinstance(layer, str) for layer in layers):
        raise SystemExit(f"{label}.layers must be a non-empty list of strings")
    invalid_layers = [layer for layer in layers if layer not in LAYERS]
    if invalid_layers:
        raise SystemExit(f"{label}.layers contain unknown layer(s): {', '.join(invalid_layers)}")
    focus_terms = source_need.get("focus_terms")
    if not isinstance(focus_terms, list) or not focus_terms or not all(isinstance(term, str) and term.strip() for term in focus_terms):
        raise SystemExit(f"{label}.focus_terms must be a non-empty list of strings")
    query_variants = source_need.get("query_variants")
    if (
        not isinstance(query_variants, list)
        or not 2 <= len(query_variants) <= 4
        or not all(isinstance(query, str) and query.strip() for query in query_variants)
    ):
        raise SystemExit(f"{label}.query_variants must contain 2-4 non-empty agent-generated query strings")


def _validate_query_variants_executed(source_need: dict[str, Any], queries: list[str], label: str) -> None:
    query_variants = source_need.get("query_variants")
    if not isinstance(query_variants, list):
        return
    executed = {_normalize_query_text(query) for query in queries}
    missing = [variant for variant in query_variants if _normalize_query_text(variant) not in executed]
    if missing:
        raise SystemExit(f"{label}.queries must include every source_need.query_variants entry")


def _normalize_query_text(value: str) -> str:
    return " ".join(value.split()).lower()


def _session_finish_warnings(source_events: list[dict[str, Any]], cited_chunk_ids: list[str], metadata: dict[str, Any]) -> list[str]:
    warnings = []
    event_chunk_ids = _source_event_chunk_ids(source_events)
    external_citations = metadata.get("external_cited_chunk_ids", [])
    if external_citations is None:
        external_citations = []
    if not isinstance(external_citations, list) or not all(isinstance(chunk_id, str) for chunk_id in external_citations):
        raise SystemExit("record-json metadata.external_cited_chunk_ids must be a list of strings when supplied")
    allowed_external = set(external_citations)
    missing = [chunk_id for chunk_id in cited_chunk_ids if chunk_id not in event_chunk_ids and chunk_id not in allowed_external]
    if missing:
        raise SystemExit("record-json cited_chunk_ids not found in source_events chunks: " + ", ".join(missing))
    if event_chunk_ids and not cited_chunk_ids:
        warnings.append("source_events include inspected chunks but cited_chunk_ids is empty")
    return warnings


def _source_event_chunk_ids(source_events: list[dict[str, Any]]) -> set[str]:
    chunk_ids: set[str] = set()
    for event in source_events:
        for chunk in event.get("chunks", []):
            chunk_id = chunk.get("id")
            if isinstance(chunk_id, str):
                chunk_ids.add(chunk_id)
    return chunk_ids


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _parse_source_need(value: Any) -> SourceNeed:
    if not isinstance(value, dict):
        raise SystemExit("source-need-json must decode to an object")
    intent = value.get("intent")
    layers = value.get("layers", [])
    focus_terms = value.get("focus_terms", [])
    user_turn = value.get("user_turn", "")
    query_variants = value.get("query_variants", [])
    if not isinstance(intent, str) or not intent:
        raise SystemExit("source need requires non-empty string field: intent")
    if not isinstance(layers, list) or not all(isinstance(layer, str) for layer in layers):
        raise SystemExit("source need field layers must be a list of strings")
    if not isinstance(focus_terms, list) or not all(isinstance(term, str) for term in focus_terms):
        raise SystemExit("source need field focus_terms must be a list of strings")
    if not isinstance(user_turn, str):
        raise SystemExit("source need field user_turn must be a string when supplied")
    if not isinstance(query_variants, list) or not all(isinstance(query, str) for query in query_variants):
        raise SystemExit("source need field query_variants must be a list of strings when supplied")
    invalid_layers = [layer for layer in layers if layer not in LAYERS]
    if invalid_layers:
        raise SystemExit(f"unknown source need layer(s): {', '.join(invalid_layers)}")
    return SourceNeed(
        intent=intent,
        layers=tuple(layers),
        focus_terms=tuple(focus_terms),
        user_turn=user_turn,
        query_variants=tuple(query_variants),
    )


def _search_index(
    index: CorpusIndex,
    query: str,
    *,
    layer: str | None,
    top_k: int,
    backend: str,
    vector_store: str = "local",
):
    if backend == "bm25":
        return index.search(query, layer=layer, top_k=top_k)
    if backend == "vector":
        return index.vector_search(query, layer=layer, top_k=top_k, vector_store_name=vector_store)
    if backend == "hybrid":
        return index.hybrid_search(query, layer=layer, top_k=top_k, vector_store_name=vector_store)
    raise SystemExit(f"unknown retrieval backend: {backend}")


def _source_need_to_dict(source_need: SourceNeed) -> dict[str, Any]:
    return {
        "intent": source_need.intent,
        "layers": list(source_need.layers),
        "focus_terms": list(source_need.focus_terms),
        "user_turn": source_need.user_turn,
        "query_variants": list(source_need.query_variants),
    }


def _write_turn_record(sessions_dir: Path, payload: dict[str, Any]) -> Path:
    timestamp = payload["created_at"].replace(":", "").replace("-", "").replace("Z", "")
    existing = len(list(sessions_dir.glob(f"{timestamp}*.json")))
    suffix = f"_{existing + 1:02d}" if existing else ""
    path = sessions_dir / f"{timestamp}{suffix}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _advisor_state_summary(snapshot: BusinessSnapshot) -> dict[str, Any]:
    payload = snapshot.to_dict()
    advisor_state = payload["advisor_state"]
    return {
        "advisory_status": advisor_state["advisory_status"],
        "ready_for_payback_diagnosis": advisor_state["ready_for_payback_diagnosis"],
        "ready_for_offer_stack_diagnosis": advisor_state["ready_for_offer_stack_diagnosis"],
        "missing_fields": advisor_state["missing_fields"],
        "likely_retrieval_layers": advisor_state["likely_retrieval_layers"],
        "retrieval_query_terms": _compact_list(advisor_state["retrieval_query_terms"], 8),
        "known_facts": _known_snapshot_facts(payload),
    }


def _known_snapshot_facts(snapshot_payload: dict[str, Any]) -> dict[str, Any]:
    known: dict[str, Any] = {}
    for section_name in ("business", "economics"):
        for key, value in snapshot_payload.get(section_name, {}).items():
            _add_known_fact(known, f"{section_name}.{key}", value)
    problem = snapshot_payload.get("problem", {})
    _add_known_fact(known, "problem.user_goal", problem.get("user_goal"))
    symptoms = problem.get("reported_symptoms", [])
    if symptoms:
        known["problem.reported_symptoms_count"] = len(symptoms)
        known["problem.recent_reported_symptoms"] = symptoms[-3:]
    constraints = problem.get("diagnosed_constraints", [])
    if constraints:
        known["problem.diagnosed_constraints"] = constraints
    for position, values in snapshot_payload.get("money_model", {}).items():
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            _add_known_fact(known, f"money_model.{position}.{key}", value)
    return known


def _add_known_fact(known: dict[str, Any], field_name: str, value: Any) -> None:
    if value is None or value == "" or value == []:
        return
    known[field_name] = value


def _recent_turn_summaries(sessions_dir: Path, limit: int) -> list[dict[str, Any]]:
    summaries = []
    for path in sorted(sessions_dir.glob("*.json"), reverse=True)[:limit]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        summaries.append(_session_turn_summary(path, payload))
    return summaries


def _session_turn_summary(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    summary = _summarize_log(path, payload)
    return {
        "path": summary["path"],
        "created_at": summary["created_at"],
        "user_message": _truncate_text(summary.get("user_message"), 180),
        "assistant_message": _truncate_text(summary.get("assistant_message"), 360),
        "actions": summary["actions"],
        "source_event_count": len(summary["source_events"]),
        "source_chunk_ids": summary["source_chunk_ids"],
    }


def _compact_list(values: list[Any], limit: int) -> list[Any]:
    compacted = [_truncate_text(value, 120) for value in values]
    if len(values) <= limit:
        return compacted
    return [*compacted[:limit], f"... {len(values) - limit} more"]


def _truncate_text(value: Any, limit: int) -> Any:
    if not isinstance(value, str) or len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


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
        "calculation_events": payload.get("calculation_events", []),
        "source_chunk_ids": source_ids,
    }


if __name__ == "__main__":
    raise SystemExit(main())
