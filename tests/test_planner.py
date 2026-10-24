from datetime import date, timedelta

import pytest

from app.ideas import OfflineIdeaGenerator
from app.planner import build_plan


def test_plan_contains_every_section(make_request):
    plan = build_plan(make_request(), OfflineIdeaGenerator())
    assert plan.budget and plan.timeline and plan.vendors
    assert plan.ideas.source == "offline"


def test_summary_numbers(make_request):
    plan = build_plan(make_request(guest_count=100, total_budget=500_000), OfflineIdeaGenerator())
    assert plan.summary.budget_per_guest == 5000
    assert plan.summary.days_until_event == 200
    assert plan.summary.warnings == []


def test_short_notice_adds_a_warning(make_request):
    soon = (date.today() + timedelta(days=20)).isoformat()
    plan = build_plan(make_request(event_date=soon), OfflineIdeaGenerator())
    assert plan.summary.warnings
    assert "20 days" in plan.summary.warnings[0]


def test_event_in_the_past_is_refused(make_request):
    request = make_request()
    with pytest.raises(ValueError):
        build_plan(request, OfflineIdeaGenerator(), today=request.event_date)
