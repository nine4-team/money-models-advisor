"""Advisor runtime search-request policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdvisorQuery:
    intent: str
    subjects: tuple[str, ...]
    target_namespaces: tuple[str, ...]
    query: str
    reason: str

    @property
    def subject(self) -> str | None:
        return self.subjects[0] if len(self.subjects) == 1 else None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["subject"] = self.subject
        return payload


@dataclass(frozen=True)
class SearchRequest:
    """Agent-authored request for one corpus-guided, unfiltered search."""

    intent: str
    user_turn: str
    query: str


def build_advisor_queries(search_request: SearchRequest) -> list[AdvisorQuery]:
    """Convert the active search contract into its single executable query."""

    return [
        AdvisorQuery(
            intent=search_request.intent,
            subjects=(),
            target_namespaces=(),
            query=search_request.query,
            reason="Corpus-guided query authored by the agent for the current question.",
        )
    ]
