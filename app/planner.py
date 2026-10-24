"""Orchestrates budget, timeline, vendors and ideas into one plan.

``build_plan`` is a pure function of its inputs (the idea generator and
"today" are injected), which makes it trivial to test without network or clock.
"""
from __future__ import annotations

from datetime import date

from app.budget import allocate_budget
from app.catalog import BLUEPRINTS
from app.ideas import IdeaGenerator
from app.models import EventPlan, PlanRequest, PlanSummary
from app.timeline import build_timeline
from app.vendors import build_vendor_checklist


def build_plan(request: PlanRequest, idea_generator: IdeaGenerator, today: date | None = None) -> EventPlan:
    today = today or date.today()
    days_until = (request.event_date - today).days
    if days_until < 1:
        raise ValueError("event_date must be after today")

    blueprint = BLUEPRINTS[request.event_type]
    warnings: list[str] = []
    if days_until < blueprint.min_recommended_days:
        warnings.append(
            f"Only {days_until} days to go; {blueprint.min_recommended_days}+ is ideal for a "
            f"{request.event_type.value}. Dates below are compressed, so book high-priority vendors first."
        )

    return EventPlan(
        request=request,
        summary=PlanSummary(
            days_until_event=days_until,
            budget_per_guest=round(request.total_budget / request.guest_count, 2),
            warnings=warnings,
        ),
        budget=allocate_budget(request.event_type, request.total_budget, request.guest_count),
        timeline=build_timeline(request.event_type, request.event_date, today),
        vendors=build_vendor_checklist(request.event_type, request.event_date, today),
        ideas=idea_generator.generate(request),
    )
