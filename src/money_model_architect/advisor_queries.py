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
    query_variants: tuple[str, ...] = ()


def build_advisor_queries(snapshot: BusinessSnapshot, source_need: SourceNeed) -> list[AdvisorQuery]:
    """Build source-material queries from an explicit agent-selected source need."""

    return _source_need_queries(snapshot, source_need)


def _source_need_queries(snapshot: BusinessSnapshot, source_need: SourceNeed) -> list[AdvisorQuery]:
    terms = [*source_need.focus_terms, *_compact_context_terms(snapshot)]
    layer = source_need.layers[0] if len(source_need.layers) == 1 else None

    queries: list[AdvisorQuery] = []
    for variant in source_need.query_variants:
        variant_text = _join_terms([variant])
        if not variant_text:
            continue
        queries.append(
            AdvisorQuery(
                intent=source_need.intent,
                layer=layer,
                query=variant_text,
                reason="Agent-generated query variant for the selected source need.",
            )
        )

    fallback_text = _join_terms(terms)
    if not fallback_text:
        return queries
    queries.append(
        AdvisorQuery(
            intent=source_need.intent,
            layer=layer,
            query=fallback_text,
            reason="Deterministic fallback query from source-need focus terms and compact business context.",
        )
    )
    return _dedupe_queries(queries)


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
        key = (query.layer, query.query.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(query)
    return deduped
