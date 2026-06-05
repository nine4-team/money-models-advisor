"""BusinessSnapshot v1 schema and persistence helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .calculator import payback_period_months

SCHEMA_VERSION = "business_snapshot.v1"
STACK_POSITIONS = ("attraction_offer", "core_offer", "upsell", "downsell", "continuity")


@dataclass
class BusinessInfo:
    business_type: str | None = None
    icp: str | None = None
    delivery_model: str | None = None


@dataclass
class StackPosition:
    exists: bool | None = None
    description: str | None = None
    price: float | None = None


@dataclass
class MoneyModel:
    attraction_offer: StackPosition = field(default_factory=StackPosition)
    core_offer: StackPosition = field(default_factory=StackPosition)
    upsell: StackPosition = field(default_factory=StackPosition)
    downsell: StackPosition = field(default_factory=StackPosition)
    continuity: StackPosition = field(default_factory=StackPosition)


@dataclass
class Economics:
    cac: float | None = None
    first_30_day_gross_profit: float | None = None
    monthly_recurring_gross_profit: float | None = None
    gross_margin: float | None = None
    lifetime_gross_profit: float | None = None
    payback_period_months: float | None = None


@dataclass
class ProblemState:
    user_goal: str | None = None
    reported_symptoms: list[str] = field(default_factory=list)
    diagnosed_constraints: list[str] = field(default_factory=list)


@dataclass
class AdvisorState:
    advisory_status: str = "insufficient_context"
    missing_fields: list[str] = field(default_factory=list)
    ready_for_payback_diagnosis: bool = False
    ready_for_offer_stack_diagnosis: bool = False
    likely_retrieval_layers: list[str] = field(default_factory=list)
    retrieval_query_terms: list[str] = field(default_factory=list)


@dataclass
class BusinessSnapshot:
    schema_version: str = SCHEMA_VERSION
    business: BusinessInfo = field(default_factory=BusinessInfo)
    money_model: MoneyModel = field(default_factory=MoneyModel)
    economics: Economics = field(default_factory=Economics)
    problem: ProblemState = field(default_factory=ProblemState)
    advisor_state: AdvisorState = field(default_factory=AdvisorState)
    field_sources: dict[str, dict[str, Any]] = field(default_factory=dict)

    def refresh(self) -> None:
        """Recompute derived fields, readiness flags, missing fields, and retrieval hints."""
        self._refresh_calculated_fields()
        missing = self._missing_fields()
        self.advisor_state.missing_fields = missing
        self.advisor_state.ready_for_payback_diagnosis = not any(
            field_name in missing
            for field_name in (
                "problem.user_goal",
                "business.business_type",
                "money_model.core_offer.description",
                "economics.cac",
                "economics.first_30_day_gross_profit",
            )
        )
        self.advisor_state.ready_for_offer_stack_diagnosis = not any(
            field_name in missing
            for field_name in (
                "problem.user_goal",
                "business.business_type",
                "business.icp",
                "money_model.core_offer.description",
                "money_model.attraction_offer.exists",
                "money_model.upsell.exists",
                "money_model.downsell.exists",
                "money_model.continuity.exists",
            )
        )
        self.advisor_state.advisory_status = self._advisory_status()
        self.advisor_state.likely_retrieval_layers = self._likely_layers()
        self.advisor_state.retrieval_query_terms = self._query_terms()

    def to_dict(self) -> dict[str, Any]:
        self.refresh()
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BusinessSnapshot":
        snapshot = cls(
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            business=BusinessInfo(**payload.get("business", {})),
            money_model=_money_model_from_dict(payload.get("money_model", {})),
            economics=Economics(**payload.get("economics", {})),
            problem=ProblemState(**payload.get("problem", {})),
            advisor_state=AdvisorState(**payload.get("advisor_state", {})),
            field_sources=payload.get("field_sources", {}),
        )
        snapshot.refresh()
        return snapshot

    @classmethod
    def load(cls, path: Path) -> "BusinessSnapshot":
        if not path.exists():
            snapshot = cls()
            snapshot.refresh()
            return snapshot
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _refresh_calculated_fields(self) -> None:
        econ = self.economics
        if econ.cac is None or econ.first_30_day_gross_profit is None:
            return
        monthly_gp = econ.monthly_recurring_gross_profit or 0.0
        payback = payback_period_months(econ.cac, econ.first_30_day_gross_profit, monthly_gp)
        if payback == float("inf"):
            econ.payback_period_months = None
        else:
            econ.payback_period_months = payback
        self.field_sources["economics.payback_period_months"] = {
            "source_type": "calculated",
            "inputs": [
                "economics.cac",
                "economics.first_30_day_gross_profit",
                "economics.monthly_recurring_gross_profit",
            ],
            "confidence": "high",
        }

    def _missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.problem.user_goal:
            missing.append("problem.user_goal")
        if not self.business.business_type:
            missing.append("business.business_type")
        if not self.business.icp:
            missing.append("business.icp")
        if not self.money_model.core_offer.description:
            missing.append("money_model.core_offer.description")
        for position in ("attraction_offer", "upsell", "downsell", "continuity"):
            if getattr(self.money_model, position).exists is None:
                missing.append(f"money_model.{position}.exists")
        if self.economics.cac is None:
            missing.append("economics.cac")
        if self.economics.first_30_day_gross_profit is None:
            missing.append("economics.first_30_day_gross_profit")
        return missing

    def _advisory_status(self) -> str:
        if self.problem.diagnosed_constraints and self.advisor_state.ready_for_offer_stack_diagnosis:
            return "recommendable"
        if self.problem.diagnosed_constraints:
            return "diagnosed"
        if self.advisor_state.ready_for_payback_diagnosis:
            return "diagnosable"
        return "insufficient_context"

    def _likely_layers(self) -> list[str]:
        layers: list[str] = []
        text = " ".join([self.problem.user_goal or "", *self.problem.reported_symptoms]).lower()
        if any(term in text for term in ("cac", "payback", "cash", "margin", "gross profit", "ltv", "economics")):
            layers.append("unit-economics")
        if any(term in text for term in ("lead", "ad", "attraction", "free", "trial", "front end")):
            layers.append("offers")
        if any(term in text for term in ("upsell", "backend", "after first sale")):
            layers.append("upsells")
        if any(term in text for term in ("downsell", "refund", "payment plan", "financing")):
            layers.append("downsells")
        if any(term in text for term in ("continuity", "recurring", "churn", "retention", "subscription")):
            layers.append("continuity")
        return _dedupe(layers)

    def _query_terms(self) -> list[str]:
        terms: list[str] = []
        for value in (
            self.business.business_type,
            self.business.icp,
            self.money_model.core_offer.description,
            self.problem.user_goal,
            *self.problem.reported_symptoms,
            *self.problem.diagnosed_constraints,
        ):
            if value:
                terms.append(value)
        if self.economics.cac is not None:
            terms.append("CAC")
        if self.economics.first_30_day_gross_profit is not None:
            terms.append("first 30 day gross profit")
        if self.economics.payback_period_months is not None:
            terms.append("payback period")
        return _dedupe(terms)


def _money_model_from_dict(payload: dict[str, Any]) -> MoneyModel:
    kwargs = {}
    for position in STACK_POSITIONS:
        value = payload.get(position, {})
        kwargs[position] = StackPosition(**value) if isinstance(value, dict) else StackPosition()
    return MoneyModel(**kwargs)


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
