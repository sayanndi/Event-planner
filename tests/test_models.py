from datetime import date

import pytest
from pydantic import ValidationError

from app.models import PlanRequest


def test_valid_request_is_accepted(make_request):
    assert make_request().guest_count == 150


@pytest.mark.parametrize(
    "overrides",
    [
        {"event_date": date.today().isoformat()},  # today is not "in the future"
        {"event_date": "2000-01-01"},
        {"guest_count": 0},
        {"guest_count": 5001},
        {"total_budget": 0},
        {"total_budget": -50},
        {"total_budget": float("nan")},
        {"total_budget": float("inf")},
        {"currency": "inr"},
        {"currency": "RUPEES"},
        {"title": "   "},
        {"title": "x" * 81},
        {"preferences": "x" * 501},
        {"event_type": "funeral"},
        {"is_admin": True},  # unknown fields are rejected
    ],
)
def test_invalid_requests_are_rejected(make_payload, overrides):
    with pytest.raises(ValidationError):
        PlanRequest.model_validate(make_payload(**overrides))


def test_text_is_trimmed(make_payload):
    request = PlanRequest.model_validate(make_payload(title="  Party  ", location="  Pune "))
    assert (request.title, request.location) == ("Party", "Pune")
