import pytest

from app.budget import allocate_budget
from app.catalog import BLUEPRINTS
from app.models import EventType

ALL_TYPES = list(EventType)


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_catalog_percentages_total_100(event_type):
    assert sum(BLUEPRINTS[event_type].budget_split.values()) == 100


@pytest.mark.parametrize("event_type", ALL_TYPES)
@pytest.mark.parametrize("total", [1, 999.99, 100000.01, 1_234_567.89, 1_000_000_000])
def test_lines_add_up_exactly_to_total(event_type, total):
    lines = allocate_budget(event_type, total, guest_count=77)
    assert sum(round(line.amount * 100) for line in lines) == round(total * 100)


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_every_plan_reserves_a_contingency(event_type):
    categories = [line.category for line in allocate_budget(event_type, 100_000, 50)]
    assert "Contingency" in categories


def test_amounts_are_never_negative_and_per_guest_is_consistent():
    lines = allocate_budget(EventType.BIRTHDAY, 10_000, guest_count=40)
    assert all(line.amount >= 0 for line in lines)
    assert lines[0].per_guest == pytest.approx(lines[0].amount / 40, abs=0.01)


def test_rejects_zero_guests():
    with pytest.raises(ValueError):
        allocate_budget(EventType.WEDDING, 1000, guest_count=0)
