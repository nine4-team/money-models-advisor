"""First stateful advisor skeleton over BusinessSnapshot v1."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .advisor_queries import build_advisor_queries
from .advisor_retrieval import execute_advisor_queries
from .business_context import advisor_paths, ensure_advisor_state, utc_now
from .snapshot import BusinessSnapshot

MONEY_RE = re.compile(r"\$?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)")

FIELD_QUESTIONS: dict[str, str] = {
    "problem.user_goal": "What do you want the advisor to help you decide or improve?",
    "business.business_type": "What kind of business is this?",
    "business.icp": "Who is the ICP or customer segment?",
    "money_model.core_offer.description": "What is the core offer you sell first?",
    "money_model.attraction_offer.exists": "Do you currently have an attraction offer before the core sale?",
    "money_model.upsell.exists": "Do you currently have an upsell after the core sale?",
    "money_model.downsell.exists": "Do you currently have a downsell or payment-plan/save option?",
    "money_model.continuity.exists": "Do you currently have a continuity or recurring offer?",
    "economics.cac": "What is your CAC?",
    "economics.first_30_day_gross_profit": "What is the first-30-day gross profit from the first sale?",
}

PAYBACK_PRIORITY = (
    "problem.user_goal",
    "business.business_type",
    "money_model.core_offer.description",
    "economics.cac",
    "economics.first_30_day_gross_profit",
)

STACK_PRIORITY = (
    "problem.user_goal",
    "business.business_type",
    "business.icp",
    "money_model.core_offer.description",
    "money_model.attraction_offer.exists",
    "money_model.upsell.exists",
    "money_model.downsell.exists",
    "money_model.continuity.exists",
)


@dataclass
class AdvisorTurn:
    user_message: str
    assistant_message: str
    snapshot: dict[str, Any]
    actions: list[str] = field(default_factory=list)
    retrieval_queries: list[dict[str, str]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)


def run_single_turn(business_dir: Path, message: str, transcript_dir: Path | None = None) -> AdvisorTurn:
    paths = advisor_paths(business_dir)
    ensure_advisor_state(paths)

    snapshot = BusinessSnapshot.load(paths.snapshot)
    actions = update_snapshot_from_message(snapshot, message)
    snapshot.refresh()
    actions.extend(diagnose_snapshot_constraints(snapshot))

    advisor_queries = build_advisor_queries(snapshot)
    retrieval_queries = [query.to_dict() for query in advisor_queries]
    evidence = []
    if advisor_queries:
        evidence = [
            query_evidence.to_dict()
            for query_evidence in execute_advisor_queries(
                advisor_queries,
                transcript_dir=transcript_dir or _default_transcript_dir(),
            )
        ]
    assistant_message = synthesize_advisor_message(snapshot, evidence)
    snapshot.save(paths.snapshot)

    turn = AdvisorTurn(
        user_message=message,
        assistant_message=assistant_message,
        snapshot=snapshot.to_dict(),
        actions=actions,
        retrieval_queries=retrieval_queries,
        evidence=evidence,
    )
    save_session_turn(paths.sessions_dir, turn)
    return turn


def diagnose_snapshot_constraints(snapshot: BusinessSnapshot) -> list[str]:
    """Set deterministic diagnosis outputs that can be derived from the snapshot."""
    actions: list[str] = []
    if not snapshot.advisor_state.ready_for_payback_diagnosis:
        return actions
    if (
        snapshot.economics.payback_period_months is None
        and "payback_not_recovered_without_recurring_gp" not in snapshot.problem.diagnosed_constraints
    ):
        snapshot.problem.diagnosed_constraints.append("payback_not_recovered_without_recurring_gp")
        actions.append("set problem.diagnosed_constraints.payback_not_recovered_without_recurring_gp")
    snapshot.refresh()
    return actions


def update_snapshot_from_message(snapshot: BusinessSnapshot, message: str) -> list[str]:
    """Extract only obvious facts from a user message.

    This is a deterministic v1 skeleton, not the final extraction strategy. It
    updates direct, low-risk fields and leaves ambiguous facts for clarification.
    """
    actions: list[str] = []
    text = message.strip()
    lower = text.lower()

    if text and snapshot.problem.user_goal is None:
        snapshot.problem.user_goal = text
        snapshot.field_sources["problem.user_goal"] = _conversation_source("high")
        actions.append("set problem.user_goal")
    elif text and text not in snapshot.problem.reported_symptoms:
        snapshot.problem.reported_symptoms.append(text)
        actions.append("append problem.reported_symptoms")

    extracted_numbers = _extract_numeric_fields(lower)
    for field_name, value in extracted_numbers.items():
        _set_field(snapshot, field_name, value)
        snapshot.field_sources[field_name] = _conversation_source("high")
        actions.append(f"set {field_name}")

    business_type = _extract_after_patterns(lower, ("business is ", "we run a ", "we are a ", "it's a "))
    if business_type and snapshot.business.business_type is None:
        snapshot.business.business_type = business_type
        snapshot.field_sources["business.business_type"] = _conversation_source("medium")
        actions.append("set business.business_type")

    core_offer = _extract_after_patterns(lower, ("core offer is ", "main offer is ", "we sell ", "offer is "))
    if core_offer and snapshot.money_model.core_offer.description is None:
        snapshot.money_model.core_offer.exists = True
        snapshot.money_model.core_offer.description = core_offer
        snapshot.field_sources["money_model.core_offer.description"] = _conversation_source("medium")
        snapshot.field_sources["money_model.core_offer.exists"] = _conversation_source("medium")
        actions.append("set money_model.core_offer")

    _update_stack_existence(snapshot, lower, actions)
    return actions


def synthesize_advisor_message(snapshot: BusinessSnapshot, evidence: list[dict[str, Any]] | None = None) -> str:
    """Compose the visible v1 advisor answer from state, calculations, and source chunks."""
    snapshot.refresh()
    evidence = evidence or []
    missing = _prioritized_missing(snapshot)

    if snapshot.problem.diagnosed_constraints:
        return _diagnostic_or_recommendation_message(snapshot, evidence, missing)

    if snapshot.advisor_state.ready_for_payback_diagnosis:
        payback = snapshot.economics.payback_period_months
        if payback is None:
            return _join_answer_parts(
                [
                    "Diagnosis: CAC is not paid back by first-30-day gross profit, and no recurring gross profit is saved yet, so payback is currently unrecovered from the known facts.",
                    _source_sentence(evidence),
                    _next_context_sentence(missing),
                ]
            )
        return _join_answer_parts(
            [
                f"Diagnosis: estimated payback is {payback:.2f} month(s).",
                _source_sentence(evidence),
                _next_context_sentence(missing),
            ]
        )

    if missing:
        return FIELD_QUESTIONS.get(missing[0], f"I need {missing[0]} before I can diagnose this cleanly.")
    return "I have enough basic context. Next I should retrieve source evidence and produce a cited recommendation."


def next_advisor_message(snapshot: BusinessSnapshot) -> str:
    return synthesize_advisor_message(snapshot)


def _diagnostic_or_recommendation_message(
    snapshot: BusinessSnapshot,
    evidence: list[dict[str, Any]],
    missing: list[str],
) -> str:
    econ = snapshot.economics
    parts: list[str] = []

    if "payback_not_recovered_without_recurring_gp" in snapshot.problem.diagnosed_constraints:
        if econ.cac is not None and econ.first_30_day_gross_profit is not None:
            gap = econ.cac - econ.first_30_day_gross_profit
            parts.append(
                "Diagnosis: the current bottleneck is first-30-day gross profit. "
                f"CAC is {_money(econ.cac)} and first-30-day gross profit is {_money(econ.first_30_day_gross_profit)}, "
                f"so the first sale leaves {_money(max(gap, 0.0))} of CAC unrecovered."
            )
        else:
            parts.append("Diagnosis: the current bottleneck appears to be first-30-day gross profit.")
        parts.append(
            "Because no monthly recurring gross profit is saved, the advisor cannot calculate a finite payback period from the current snapshot."
        )
    elif econ.payback_period_months is not None:
        parts.append(f"Diagnosis: estimated payback is {econ.payback_period_months:.2f} month(s).")
    else:
        parts.append("Diagnosis: the snapshot is far enough along for a first constraint read, but the payback math is incomplete.")

    recommendation = _recommendation_sentence(snapshot)
    if recommendation:
        parts.append(recommendation)

    parts.append(_source_sentence(evidence))
    parts.append(_next_context_sentence(missing))
    return _join_answer_parts(parts)


def _recommendation_sentence(snapshot: BusinessSnapshot) -> str | None:
    stack = snapshot.money_model
    constraints = set(snapshot.problem.diagnosed_constraints)
    if "payback_not_recovered_without_recurring_gp" not in constraints and "slow_payback" not in constraints:
        return None

    if stack.upsell.exists is False and stack.continuity.exists is False:
        return "Recommended next move: test the smallest credible post-sale profit layer first, either an upsell that raises first-sale gross profit or a continuity offer that adds recurring gross profit."
    if stack.upsell.exists is False:
        return "Recommended next move: test an upsell after the first sale so the first customer contributes more gross profit before payback drags out."
    if stack.continuity.exists is False:
        return "Recommended next move: test a continuity offer so each acquired customer can create recurring gross profit after the first sale."
    return "Recommended next move: inspect the current upsell and continuity economics before adding another offer layer."


def _source_sentence(evidence: list[dict[str, Any]]) -> str | None:
    source_ids = _source_chunk_ids(evidence)
    if not source_ids:
        return None
    citations = " ".join(f"[{chunk_id}]" for chunk_id in source_ids[:3])
    return f"Source support: {citations}."


def _source_chunk_ids(evidence: list[dict[str, Any]]) -> list[str]:
    source_ids: list[str] = []
    for item in evidence:
        for chunk in item.get("chunks", []):
            chunk_id = chunk.get("id")
            if chunk_id and chunk_id not in source_ids:
                source_ids.append(chunk_id)
    return source_ids


def _next_context_sentence(missing: list[str]) -> str | None:
    if not missing:
        return "Next action: run the smallest offer-stack test that improves payback, then update the snapshot with the result."
    question = FIELD_QUESTIONS.get(missing[0], f"I need {missing[0]} before I can diagnose this cleanly.")
    return f"Next missing context: {question}"


def _join_answer_parts(parts: list[str | None]) -> str:
    return "\n\n".join(part for part in parts if part)


def _money(value: float) -> str:
    if value == int(value):
        return f"${int(value):,}"
    return f"${value:,.2f}"


def save_session_turn(sessions_dir: Path, turn: AdvisorTurn) -> Path:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = sessions_dir / f"{turn.created_at.replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(asdict(turn), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _prioritized_missing(snapshot: BusinessSnapshot) -> list[str]:
    missing = set(snapshot.advisor_state.missing_fields)
    priority = PAYBACK_PRIORITY if _looks_like_payback_problem(snapshot) else STACK_PRIORITY
    ordered = [field_name for field_name in priority if field_name in missing]
    ordered.extend(field_name for field_name in snapshot.advisor_state.missing_fields if field_name not in ordered)
    return ordered


def _looks_like_payback_problem(snapshot: BusinessSnapshot) -> bool:
    text = " ".join([snapshot.problem.user_goal or "", *snapshot.problem.reported_symptoms]).lower()
    return any(term in text for term in ("cac", "payback", "cash", "gross profit", "margin", "ltv", "first 30"))


def _extract_numeric_fields(lower: str) -> dict[str, float]:
    fields: dict[str, float] = {}
    patterns = {
        "economics.cac": (r"\bcac\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",),
        "economics.first_30_day_gross_profit": (
            r"first[- ]?30[- ]?day gross profit\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            r"month[- ]?one gross profit\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        ),
        "economics.monthly_recurring_gross_profit": (
            r"monthly recurring gross profit\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            r"recurring gross profit\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        ),
        "economics.gross_margin": (r"gross margin\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*%?",),
        "economics.lifetime_gross_profit": (
            r"lifetime gross profit\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            r"\bltgp\s*(?:is|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        ),
    }
    for field_name, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, lower)
            if not match:
                continue
            value = float(match.group(1).replace(",", ""))
            if field_name == "economics.gross_margin" and value > 1:
                value = value / 100
            fields[field_name] = value
            break
    return fields


def _extract_after_patterns(lower: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        if pattern not in lower:
            continue
        value = lower.split(pattern, 1)[1].strip(" .")
        value = re.split(r"[.;\n]", value, maxsplit=1)[0].strip(" .")
        return value[:140] if value else None
    return None


def _update_stack_existence(snapshot: BusinessSnapshot, lower: str, actions: list[str]) -> None:
    for position in ("attraction_offer", "upsell", "downsell", "continuity"):
        stack_position = getattr(snapshot.money_model, position)
        readable = position.replace("_", " ")
        if f"no {readable}" in lower or f"without {readable}" in lower:
            stack_position.exists = False
            snapshot.field_sources[f"money_model.{position}.exists"] = _conversation_source("high")
            actions.append(f"set money_model.{position}.exists")
        elif f"have {readable}" in lower or f"has {readable}" in lower or f"we use {readable}" in lower:
            stack_position.exists = True
            snapshot.field_sources[f"money_model.{position}.exists"] = _conversation_source("high")
            actions.append(f"set money_model.{position}.exists")


def _set_field(snapshot: BusinessSnapshot, field_name: str, value: Any) -> None:
    target: Any = snapshot
    parts = field_name.split(".")
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], value)


def _conversation_source(confidence: str) -> dict[str, str]:
    return {"source_type": "conversation", "confidence": confidence, "updated_at": utc_now()}


def _default_transcript_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "corpus" / "transcripts"
