"""Budget allocation.

Money is split in whole minor units (cents/paise) using the largest-remainder
method, so the lines always add up to exactly the total the user entered.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.catalog import BLUEPRINTS
from app.models import BudgetLine, EventType


def allocate_budget(event_type: EventType, total_budget: float, guest_count: int) -> list[BudgetLine]:
    """Split ``total_budget`` across the categories for ``event_type``."""
    if guest_count < 1:
        raise ValueError("guest_count must be at least 1")

    split = BLUEPRINTS[event_type].budget_split
    total_cents = int((Decimal(str(total_budget)) * 100).to_integral_value(ROUND_HALF_UP))

    exact = {name: Decimal(total_cents) * percent / 100 for name, percent in split.items()}
    cents = {name: int(value) for name, value in exact.items()}  # floor (values are >= 0)

    # Hand the leftover cents to the categories that lost the most when rounding down.
    leftover = total_cents - sum(cents.values())
    by_lost_fraction = sorted(exact, key=lambda name: exact[name] - cents[name], reverse=True)
    for name in by_lost_fraction[:leftover]:
        cents[name] += 1

    return [
        BudgetLine(
            category=name,
            percent=split[name],
            amount=cents[name] / 100,
            per_guest=round(cents[name] / 100 / guest_count, 2),
        )
        for name in split
    ]
