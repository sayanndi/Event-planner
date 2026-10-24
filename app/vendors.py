"""Vendor checklists: who to book, by when, and what to ask them."""
from __future__ import annotations

from datetime import date

from app.catalog import BLUEPRINTS
from app.models import EventType, VendorChecklist
from app.timeline import due_date_for

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def build_vendor_checklist(event_type: EventType, event_date: date, today: date) -> list[VendorChecklist]:
    """Vendors ordered by priority, then by how soon they must be booked."""
    blueprint = BLUEPRINTS[event_type]
    checklist = [
        VendorChecklist(
            category=template.category,
            priority=template.priority,
            book_by=due_date_for(event_date, template.days_before, blueprint.horizon_days, today),
            questions=list(template.questions),
        )
        for template in blueprint.vendors
    ]
    checklist.sort(key=lambda item: (_PRIORITY_RANK[item.priority], item.book_by))
    return checklist
