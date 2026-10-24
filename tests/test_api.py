from fastapi.testclient import TestClient

from app.config import Settings
from app.ideas import OfflineIdeaGenerator
from app.main import create_app
from app.security import RateLimiter


def test_health(client):
    body = client.get("/api/health").json()
    assert body == {"status": "ok", "ai_enabled": False}


def test_plan_endpoint_returns_a_full_plan(client, make_payload):
    response = client.post("/api/plan", json=make_payload(event_type="community", guest_count=300))
    assert response.status_code == 200
    plan = response.json()
    assert {"summary", "budget", "timeline", "vendors", "ideas"} <= plan.keys()
    assert round(sum(line["amount"] for line in plan["budget"]), 2) == 1_500_000


def test_invalid_input_gets_a_422_with_field_details(client, make_payload):
    response = client.post("/api/plan", json=make_payload(guest_count=-3))
    assert response.status_code == 422
    assert "guest_count" in str(response.json()["detail"])


def test_unknown_fields_are_refused(client, make_payload):
    assert client.post("/api/plan", json=make_payload(admin=True)).status_code == 422


def test_oversized_body_is_refused(client):
    response = client.post("/api/plan", content=b"x" * 20_000, headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_security_headers_are_set(client):
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in headers["content-security-policy"]


def test_script_in_input_is_returned_as_data_not_executed(client, make_payload):
    payload = make_payload(title="<script>alert(1)</script>")
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_rate_limit_returns_429(make_payload):
    app = create_app(Settings(rate_limit_per_minute=2), OfflineIdeaGenerator())
    limited = TestClient(app)
    codes = [limited.post("/api/plan", json=make_payload()).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_web_page_and_assets_are_served(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "Event Planner" in page.text
    assert client.get("/app.js").status_code == 200
    assert client.get("/style.css").status_code == 200


def test_page_has_no_inline_script_or_innerhtml(client):
    assert "<script>" not in client.get("/").text
    assert "innerHTML" not in client.get("/app.js").text


def test_api_docs_are_not_exposed(client):
    assert client.get("/openapi.json").status_code == 404


# ------------------------------------------------------------- rate limiter


def test_rate_limiter_window_slides():
    now = [0.0]
    limiter = RateLimiter(limit=2, window=60, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")  # other clients are unaffected
    now[0] = 61
    assert limiter.allow("a")
