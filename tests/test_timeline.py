from datetime import date, timedelta

import pytest

from app.catalog import BLUEPRINTS
from app.models import EventType
from app.timeline import build_timeline, scale_offset
from app.vendors import build_vendor_checklist

TODAY = date(2026, 1, 1)


@pytest.mark.parametrize("event_type", list(EventType))
def test_catalog_lead_times_fit_inside_the_horizon(event_type):
    blueprint = BLUEPRINTS[event_type]
    offsets = [m.days_before for m in blueprint.milestones] + [v.days_before for v in blueprint.vendors]
    assert max(offsets) <= blueprint.horizon_days


@pytest.mark.parametrize(
    ("days_before", "horizon", "days_until", "expected"),
    [(90, 270, 270, 90), (90, 270, 500, 90), (90, 270, 135, 45), (270, 270, 0, 0)],
)
def test_scale_offset(days_before, horizon, days_until, expected):
    assert scale_offset(days_before, horizon, days_until) == expected


def test_plenty_of_time_uses_ideal_lead_times():
    event = TODAY + timedelta(days=300)
    timeline = build_timeline(EventType.WEDDING, event, TODAY)
    assert timeline[0].days_before_event == 270
    assert [m.due_date for m in timeline] == sorted(m.due_date for m in timeline)


@pytest.mark.parametrize("event_type", list(EventType))
@pytest.mark.parametrize("days_until", [1, 5, 20, 60, 400])
def test_nothing_is_ever_scheduled_in_the_past_or_after_the_event(event_type, days_until):
    event = TODAY + timedelta(days=days_until)
    for item in build_timeline(event_type, event, TODAY):
        assert TODAY <= item.due_date <= event
    for vendor in build_vendor_checklist(event_type, event, TODAY):
        assert TODAY <= vendor.book_by <= event


def test_compressed_timeline_keeps_the_task_order():
    event = TODAY + timedelta(days=30)
    titles = [m.title for m in build_timeline(EventType.WEDDING, event, TODAY)]
    ideal = [m.title for m in BLUEPRINTS[EventType.WEDDING].milestones]
    assert titles == ideal


def test_vendors_list_high_priority_first():
    event = TODAY + timedelta(days=300)
    ranks = {"high": 0, "medium": 1, "low": 2}
    priorities = [ranks[v.priority] for v in build_vendor_checklist(EventType.WEDDING, event, TODAY)]
    assert priorities == sorted(priorities)
