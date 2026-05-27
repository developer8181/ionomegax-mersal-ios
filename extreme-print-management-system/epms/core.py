"""Core business rules for Extreme Print Management System."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class PrintCostPolicy:
    bw_page_cents: int
    color_page_cents: int
    duplex_discount_percent: int = 10


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    balance_after_cents: int
    reason: str


def money_to_cents(value: str | int | float | Decimal) -> int:
    """Convert a money amount to integer cents using normal currency rounding."""
    amount = Decimal(str(value))
    return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def cents_to_money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    absolute = abs(cents)
    return f"{sign}{absolute // 100}.{absolute % 100:02d}"


def calculate_job_cost(
    *,
    pages: int,
    copies: int,
    color: bool,
    duplex: bool,
    policy: PrintCostPolicy,
) -> int:
    if pages <= 0:
        raise ValueError("pages must be greater than zero")
    if copies <= 0:
        raise ValueError("copies must be greater than zero")
    if policy.bw_page_cents < 0 or policy.color_page_cents < 0:
        raise ValueError("page costs cannot be negative")

    page_cost = policy.color_page_cents if color else policy.bw_page_cents
    subtotal = pages * copies * page_cost
    if duplex:
        discount = Decimal(subtotal) * Decimal(policy.duplex_discount_percent) / Decimal("100")
        subtotal -= int(discount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(subtotal, 0)


def evaluate_quota(*, balance_cents: int, overdraft_cents: int, cost_cents: int) -> QuotaDecision:
    if overdraft_cents < 0:
        raise ValueError("overdraft cannot be negative")
    if cost_cents < 0:
        raise ValueError("cost cannot be negative")

    balance_after = balance_cents - cost_cents
    if balance_after < -overdraft_cents:
        return QuotaDecision(
            allowed=False,
            balance_after_cents=balance_after,
            reason="Insufficient print quota",
        )
    return QuotaDecision(allowed=True, balance_after_cents=balance_after, reason="Allowed")
