"""Advisor runtime query policy v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .snapshot import BusinessSnapshot


@dataclass(frozen=True)
class AdvisorQuery:
    intent: str
    layer: str | None
    query: str
    reason: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True)
class SourceNeed:
    """Planner-selected source support for one source-material search call."""

    intent: str
    layers: tuple[str, ...]
    focus_terms: tuple[str, ...]
    user_turn: str = ""


def build_advisor_queries(snapshot: BusinessSnapshot, source_need: SourceNeed | None = None) -> list[AdvisorQuery]:
    if source_need is not None:
        return _source_need_queries(snapshot, source_need)

    snapshot.refresh()
    status = snapshot.advisor_state.advisory_status
    if status == "insufficient_context":
        return []
    if status == "diagnosable":
        return [_diagnostic_query(snapshot)]
    if status in {"diagnosed", "recommendable"}:
        return _recommendation_queries(snapshot)
    return []


def _source_need_queries(snapshot: BusinessSnapshot, source_need: SourceNeed) -> list[AdvisorQuery]:
    terms = [*source_need.focus_terms, *_compact_context_terms(snapshot)]
    query_text = _join_terms(terms)
    if not query_text:
        return []

    layer = source_need.layers[0] if len(source_need.layers) == 1 else None
    return [
        AdvisorQuery(
            intent=source_need.intent,
            layer=layer,
            query=query_text,
            reason="Source need was selected for the current turn; retrieve source-specific Money Models support.",
        )
    ]


def _diagnostic_query(snapshot: BusinessSnapshot) -> AdvisorQuery:
    terms = [
        "CAC",
        "first 30 day gross profit",
        "payback period",
        "client financed acquisition",
        "gross profit",
        snapshot.business.business_type,
        snapshot.business.icp,
        snapshot.money_model.core_offer.description,
    ]
    return AdvisorQuery(
        intent="diagnostic_evidence",
        layer="unit-economics",
        query=_join_terms(terms),
        reason="Snapshot is diagnosable; retrieve unit-economics evidence before explaining the diagnosis.",
    )


def _recommendation_queries(snapshot: BusinessSnapshot) -> list[AdvisorQuery]:
    queries: list[AdvisorQuery] = []
    constraints = set(snapshot.problem.diagnosed_constraints)
    stack = snapshot.money_model
    context = [snapshot.business.business_type, snapshot.business.icp, stack.core_offer.description]

    if {"payback_not_recovered_without_recurring_gp", "slow_payback"} & constraints:
        if stack.upsell.exists is False:
            queries.append(
                AdvisorQuery(
                    intent="recommendation_evidence",
                    layer="upsells",
                    query=_join_terms(
                        [
                            "upsell after first sale",
                            "increase first 30 day gross profit",
                            "improve payback period",
                            *context,
                        ]
                    ),
                    reason="Payback constraint and no upsell in the saved money model.",
                )
            )
        if stack.continuity.exists is False:
            queries.append(
                AdvisorQuery(
                    intent="recommendation_evidence",
                    layer="continuity",
                    query=_join_terms(
                        [
                            "continuity recurring gross profit",
                            "improve payback period",
                            "recurring offer",
                            *context,
                        ]
                    ),
                    reason="Payback constraint and no continuity offer in the saved money model.",
                )
            )

    if "weak_first_sale_monetization" in constraints:
        queries.append(
            AdvisorQuery(
                intent="recommendation_evidence",
                layer="upsells",
                query=_join_terms(["increase first sale monetization", "upsell offer", "first 30 day gross profit", *context]),
                reason="Diagnosed weak first-sale monetization.",
            )
        )

    if "low_gross_margin" in constraints:
        queries.append(
            AdvisorQuery(
                intent="recommendation_evidence",
                layer="unit-economics",
                query=_join_terms(["gross margin", "gross profit", "fulfillment cost", "margin improvement", *context]),
                reason="Diagnosed low gross margin.",
            )
        )

    if "weak_acquisition_offer" in constraints:
        queries.append(
            AdvisorQuery(
                intent="recommendation_evidence",
                layer="offers",
                query=_join_terms(["attraction offer", "free trial", "free giveaway", "front end offer", *context]),
                reason="Diagnosed weak acquisition offer.",
            )
        )

    if "refund_or_payment_resistance" in constraints:
        queries.append(
            AdvisorQuery(
                intent="recommendation_evidence",
                layer="downsells",
                query=_join_terms(["downsell", "payment plan", "pay less now", "waived fee", *context]),
                reason="Diagnosed refund or payment resistance.",
            )
        )

    if "retention_or_churn_issue" in constraints:
        queries.append(
            AdvisorQuery(
                intent="recommendation_evidence",
                layer="continuity",
                query=_join_terms(["continuity offer", "retention", "recurring value", "churn", *context]),
                reason="Diagnosed retention or churn issue.",
            )
        )

    if queries:
        return _dedupe_queries(queries)

    fallback_layer = snapshot.advisor_state.likely_retrieval_layers[0] if snapshot.advisor_state.likely_retrieval_layers else "unit-economics"
    return [
        AdvisorQuery(
            intent="recommendation_evidence",
            layer=fallback_layer,
            query=_join_terms([*snapshot.problem.diagnosed_constraints, *context, snapshot.problem.user_goal]),
            reason="No constraint-specific query rule matched; using snapshot fallback terms.",
        )
    ]


def _compact_context_terms(snapshot: BusinessSnapshot) -> list[str]:
    terms: list[str] = []
    business_type = snapshot.business.business_type or ""
    core_offer = snapshot.money_model.core_offer.description or ""
    for phrase in (
        _shorten_business_context(business_type),
        _shorten_business_context(core_offer),
    ):
        if phrase:
            terms.append(phrase)
    return terms


def _shorten_business_context(value: str) -> str | None:
    lowered = value.lower()
    if "interior design" in lowered:
        return "interior design"
    if "short-term rental" in lowered or "str" in lowered:
        return "STR"
    if "coaching" in lowered:
        return "coaching"
    words = [word.strip(" ,.;:()[]") for word in value.split()]
    words = [word for word in words if word]
    if not words:
        return None
    return " ".join(words[:3])


def _join_terms(terms: list[str | None]) -> str:
    return " ".join(_dedupe([term.strip() for term in terms if term and term.strip()]))


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _dedupe_queries(queries: list[AdvisorQuery]) -> list[AdvisorQuery]:
    seen = set()
    deduped = []
    for query in queries:
        key = (query.intent, query.layer, query.query.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(query)
    return deduped
