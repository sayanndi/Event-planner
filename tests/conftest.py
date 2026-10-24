from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.ideas import OfflineIdeaGenerator
from app.main import create_app
from app.models import PlanRequest


@pytest.fixture
def make_payload():
    """Factory for a valid request body; override any field per test."""

    def _make(**overrides):
        payload = {
            "event_type": "wedding",
            "title": "Asha & Ravi",
            "event_date": (date.today() + timedelta(days=200)).isoformat(),
            "guest_count": 150,
            "total_budget": 1_500_000,
            "currency": "INR",
            "location": "Kolkata",
            "preferences": "vegetarian menu, traditional music",
        }
        payload.update(overrides)
        return payload

    return _make


@pytest.fixture
def make_request(make_payload):
    def _make(**overrides):
        return PlanRequest.model_validate(make_payload(**overrides))

    return _make


@pytest.fixture
def client():
    app = create_app(Settings(rate_limit_per_minute=1000), OfflineIdeaGenerator())
    return TestClient(app)
