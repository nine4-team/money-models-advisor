"""Deterministic formulas for Money Models unit economics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitEconomics:
    cac: float
    first_30_day_gross_profit: float = 0.0
    monthly_recurring_gross_profit: float = 0.0
    lifetime_gross_profit: float | None = None
    gross_margin: float | None = None
    service_business: bool = False


def gross_profit(price: float, cogs: float) -> float:
    return price - cogs


def gross_margin(price: float, cogs: float) -> float:
    if price <= 0:
        raise ValueError("price must be greater than zero")
    return gross_profit(price, cogs) / price


def cac(total_acquisition_cost: float, new_customers: int) -> float:
    if new_customers <= 0:
        raise ValueError("new_customers must be greater than zero")
    return total_acquisition_cost / new_customers


def lifetime_revenue(monthly_price: float, monthly_churn_rate: float) -> float:
    if monthly_churn_rate <= 0:
        raise ValueError("monthly_churn_rate must be greater than zero")
    return monthly_price / monthly_churn_rate


def lifetime_gross_profit(monthly_price: float, monthly_churn_rate: float, margin: float) -> float:
    return lifetime_revenue(monthly_price, monthly_churn_rate) * margin


def ltgp_to_cac(lifetime_gp: float, acquisition_cost: float) -> float:
    if acquisition_cost <= 0:
        raise ValueError("acquisition_cost must be greater than zero")
    return lifetime_gp / acquisition_cost


def payback_period_months(acquisition_cost: float, month_one_gp: float, monthly_recurring_gp: float) -> float:
    if acquisition_cost <= month_one_gp:
        return 1.0
    if monthly_recurring_gp <= 0:
        return float("inf")
    return 1 + (acquisition_cost - month_one_gp) / monthly_recurring_gp


def cfa_level(acquisition_cost: float, first_30_day_gp: float) -> int:
    if acquisition_cost <= 0:
        raise ValueError("acquisition_cost must be greater than zero")
    if first_30_day_gp >= 2 * acquisition_cost:
        return 3
    if first_30_day_gp >= acquisition_cost:
        return 2
    return 1
