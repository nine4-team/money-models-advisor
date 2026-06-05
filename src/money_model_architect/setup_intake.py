"""Setup/intake helpers for building BusinessSnapshot v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .business_context import advisor_paths, ensure_advisor_state, sync_business_context, utc_now
from .snapshot import BusinessSnapshot

SETUP_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("business.business_type", "What kind of business is this?", "str"),
    ("business.icp", "Who is the ICP or customer segment?", "str"),
    ("business.delivery_model", "What is the delivery model? (service, coaching, software, course, etc.)", "str"),
    ("money_model.core_offer.description", "What is the core offer you sell first?", "str"),
    ("money_model.core_offer.price", "What is the core offer price?", "float"),
    ("economics.cac", "What is your CAC?", "float"),
    ("economics.first_30_day_gross_profit", "What is first-30-day gross profit from the first sale?", "float"),
    ("economics.monthly_recurring_gross_profit", "What is monthly recurring gross profit, if any?", "float"),
    ("money_model.attraction_offer.exists", "Do you have an attraction offer before the core sale?", "bool"),
    ("money_model.upsell.exists", "Do you have an upsell after the core sale?", "bool"),
    ("money_model.downsell.exists", "Do you have a downsell or payment-plan/save option?", "bool"),
    ("money_model.continuity.exists", "Do you have a continuity or recurring offer?", "bool"),
)


def run_setup(
    business_dir: Path,
    answers: dict[str, Any] | None = None,
    interactive: bool = False,
    input_fn: Callable[[str], str] = input,
) -> tuple[BusinessSnapshot, dict[str, int]]:
    """Initialize state, record optional files, and update the snapshot."""
    paths = advisor_paths(business_dir)
    ensure_advisor_state(paths)
    _manifest, summary = sync_business_context(paths.business_dir)
    snapshot = BusinessSnapshot.load(paths.snapshot)

    if answers:
        apply_setup_answers(snapshot, answers, source_type="setup")

    if interactive:
        interactive_answers = collect_interactive_answers(snapshot, input_fn=input_fn)
        apply_setup_answers(snapshot, interactive_answers, source_type="setup")

    snapshot.save(paths.snapshot)
    return snapshot, summary


def load_answers(path_or_json: str) -> dict[str, Any]:
    candidate = Path(path_or_json)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(path_or_json)


def collect_interactive_answers(snapshot: BusinessSnapshot, input_fn: Callable[[str], str] = input) -> dict[str, Any]:
    snapshot.refresh()
    answers: dict[str, Any] = {}
    for field_name, question, value_type in SETUP_FIELDS:
        current = _get_field(snapshot, field_name)
        if current is not None:
            continue
        raw = input_fn(f"{question} ").strip()
        if raw == "":
            continue
        answers[field_name] = _parse_value(raw, value_type)
    return answers


def apply_setup_answers(snapshot: BusinessSnapshot, answers: dict[str, Any], source_type: str = "setup") -> None:
    flattened = _flatten_answers(answers)
    for field_name, raw_value in flattened.items():
        value_type = _field_type(field_name)
        value = _parse_value(raw_value, value_type)
        if value is None:
            continue
        _set_field(snapshot, field_name, value)
        if field_name.startswith("money_model.") and field_name.endswith(".description"):
            exists_field = field_name.replace(".description", ".exists")
            _set_field(snapshot, exists_field, True)
            snapshot.field_sources[exists_field] = _source_record(source_type)
        snapshot.field_sources[field_name] = _source_record(source_type)
    snapshot.refresh()


def _field_type(field_name: str) -> str:
    for candidate, _question, value_type in SETUP_FIELDS:
        if candidate == field_name:
            return value_type
    if field_name.endswith(".price") or field_name.startswith("economics."):
        return "float"
    if field_name.endswith(".exists"):
        return "bool"
    return "str"


def _parse_value(value: Any, value_type: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if value_type == "str":
        return str(value).strip()
    if value_type == "float":
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).strip().replace("$", "").replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
            return float(cleaned) / 100
        return float(cleaned)
    if value_type == "bool":
        if isinstance(value, bool):
            return value
        lowered = str(value).strip().lower()
        if lowered in {"yes", "y", "true", "1", "have", "exists"}:
            return True
        if lowered in {"no", "n", "false", "0", "none", "missing"}:
            return False
        raise ValueError(f"Cannot parse boolean value: {value!r}")
    return value


def _flatten_answers(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in payload.items():
        field_name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten_answers(value, prefix=field_name))
        else:
            flattened[field_name] = value
    return flattened


def _get_field(snapshot: BusinessSnapshot, field_name: str) -> Any:
    target: Any = snapshot
    for part in field_name.split("."):
        target = getattr(target, part)
    return target


def _set_field(snapshot: BusinessSnapshot, field_name: str, value: Any) -> None:
    target: Any = snapshot
    parts = field_name.split(".")
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], value)


def _source_record(source_type: str) -> dict[str, str]:
    return {"source_type": source_type, "confidence": "high", "updated_at": utc_now()}

