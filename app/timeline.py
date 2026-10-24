"""Timeline scheduling.

Templates describe an ideal lead time (e.g. "book the venue 240 days before").
When the event is closer than the ideal horizon, every lead time is shrunk by
the same ratio, so the order of tasks is preserved and nothing lands in the past.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.catalog import BLUEPRINTS
from app.models import EventType, Milestone


def scale_offset(days_before: int, horizon_days: int, days_until: int) -> int:
    """Shrink a lead time proportionally when there is less time than ideal."""
    if days_until >= horizon_days:
        return days_before
    return round(days_before * days_until / horizon_days)


def due_date_for(event_date: date, days_before: int, horizon_days: int, today: date) -> date:
    """Date by which something with the given ideal lead time should be done."""
    days_until = (event_date - today).days
    scaled = scale_offset(days_before, horizon_days, days_until)
    return event_date - timedelta(days=scaled)


def build_timeline(event_type: EventType, event_date: date, today: date) -> list[Milestone]:
    """Dated milestones in chronological order."""
    blueprint = BLUEPRINTS[event_type]
    milestones = []
    for index, template in enumerate(blueprint.milestones, start=1):
        due = due_date_for(event_date, template.days_before, blueprint.horizon_days, today)
        milestones.append(
            Milestone(
                id=f"t{index}",
                title=template.title,
                category=template.category,
                due_date=due,
                days_before_event=(event_date - due).days,
            )
        )
    milestones.sort(key=lambda item: item.due_date)  # stable: ties keep template order
    return milestones
