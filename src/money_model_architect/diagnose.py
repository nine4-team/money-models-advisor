"""Constraint diagnosis over deterministic unit economics."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .calculator import UnitEconomics, cfa_level, ltgp_to_cac, payback_period_months


@dataclass(frozen=True)
class Diagnosis:
    constraint: str
    tree: str
    prescribed_sections: tuple[str, ...]
    reason: str
    success_metric: str
    metrics: dict[str, float | int | str | None]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["prescribed_sections"] = list(self.prescribed_sections)
        return data


def diagnose(economics: UnitEconomics) -> Diagnosis:
    metrics: dict[str, float | int | str | None] = {
        "cac": economics.cac,
        "first_30_day_gross_profit": economics.first_30_day_gross_profit,
        "monthly_recurring_gross_profit": economics.monthly_recurring_gross_profit,
        "lifetime_gross_profit": economics.lifetime_gross_profit,
        "gross_margin": economics.gross_margin,
    }

    if economics.lifetime_gross_profit is not None:
        ratio = ltgp_to_cac(economics.lifetime_gross_profit, economics.cac)
        metrics["ltgp_to_cac"] = round(ratio, 2)
        if ratio < 1:
            return Diagnosis(
                constraint="viability",
                tree="Unit Economics",
                prescribed_sections=("1.2 How Businesses Make Money", "1.4 Gross Profit"),
                reason=f"LTGP/CAC is {ratio:.2f}:1, so each acquired customer burns gross profit.",
                success_metric="Raise LTGP/CAC above 3:1 before adding offer complexity.",
                metrics=metrics,
            )
        if ratio < 3:
            return Diagnosis(
                constraint="viability",
                tree="Unit Economics",
                prescribed_sections=("1.2 How Businesses Make Money", "1.4 Gross Profit", "6.3 Continuity Discount Offers"),
                reason=f"LTGP/CAC is {ratio:.2f}:1, below the 3:1 viability floor.",
                success_metric="Improve price, gross margin, retention, or CAC until LTGP/CAC is at least 3:1.",
                metrics=metrics,
            )

    if economics.service_business and economics.gross_margin is not None and economics.gross_margin < 0.8:
        return Diagnosis(
            constraint="gross-margin",
            tree="Unit Economics",
            prescribed_sections=("1.4 Gross Profit",),
            reason=f"Service gross margin is {economics.gross_margin:.0%}, below the 80% rule of thumb.",
            success_metric="Get service gross margin to 80%+ before layering more offers.",
            metrics=metrics,
        )

    level = cfa_level(economics.cac, economics.first_30_day_gross_profit)
    metrics["cfa_level"] = level
    payback = payback_period_months(
        economics.cac,
        economics.first_30_day_gross_profit,
        economics.monthly_recurring_gross_profit,
    )
    metrics["payback_period_months"] = "inf" if payback == float("inf") else round(payback, 2)

    if level == 1:
        return Diagnosis(
            constraint="monetization",
            tree="Tree B - Which Upsell Fits?",
            prescribed_sections=("4.1 Upsell Offers Overview", "1.5 Payback Period"),
            reason="First-30-day gross profit does not cover CAC, so the model cannot finance acquisition inside the first month.",
            success_metric="Increase first-30-day gross profit until it covers CAC, then push toward 2x CAC.",
            metrics=metrics,
        )

    if payback > 6:
        return Diagnosis(
            constraint="cash-constraint",
            tree="Tree B - Which Upsell Fits?",
            prescribed_sections=("1.5 Payback Period", "4.1 Upsell Offers Overview", "3.5 Buy X Get Y Free"),
            reason=f"Payback is {payback:.1f} months, so cash recycles too slowly even if lifetime economics work.",
            success_metric="Compress payback below one month with first-30-day upsells, prepayment, or initiation fees.",
            metrics=metrics,
        )

    if level == 2:
        return Diagnosis(
            constraint="cfa-level-2",
            tree="Tree E - What to Add Next",
            prescribed_sections=("1.6 CFA", "4.1 Upsell Offers Overview"),
            reason="The model covers CAC in 30 days but does not yet produce 2x CAC in first-30-day gross profit.",
            success_metric="Move from Level 2 to Level 3 CFA by raising first-30-day GP above 2x CAC.",
            metrics=metrics,
        )

    return Diagnosis(
        constraint="scale-ready",
        tree="Tree E - What to Add Next",
        prescribed_sections=("1.6 CFA", "6.1 Continuity Offers Overview"),
        reason="First-30-day gross profit is at least 2x CAC, so acquisition is client-financed at Level 3.",
        success_metric="Protect conversion and churn while scaling spend.",
        metrics=metrics,
    )
