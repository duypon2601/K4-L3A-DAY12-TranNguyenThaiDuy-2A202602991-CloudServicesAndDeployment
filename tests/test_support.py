"""Task 5 — Customer-support theme & /usage endpoint tests."""

from __future__ import annotations

import pytest


def test_usage_without_key_returns_401(client):
    """Calling /usage without API key must return 401 Unauthorized."""
    response = client.get("/usage")
    assert response.status_code == 401


def test_usage_fresh_customer(client, auth_headers, fake_redis):
    """A fresh customer has 0 requests, 0 spent, and full remaining budget."""
    response = client.get("/usage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == auth_headers["X-User-Id"]
    assert data["requests_last_minute"] == 0
    assert data["spent_usd"] == pytest.approx(0.0)
    assert data["monthly_budget_usd"] > 0
    assert data["budget_remaining_usd"] == pytest.approx(data["monthly_budget_usd"])


def test_usage_after_two_ask_calls(client, auth_headers):
    """After 2 /ask requests, requests_last_minute is 2 and spent_usd > 0."""
    for i in range(2):
        resp = client.post(
            "/ask", json={"question": f"Question {i}"}, headers=auth_headers
        )
        assert resp.status_code == 200

    response = client.get("/usage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["requests_last_minute"] == 2
    assert data["spent_usd"] > 0
    assert data["budget_remaining_usd"] == pytest.approx(
        data["monthly_budget_usd"] - data["spent_usd"]
    )


def test_usage_repeated_calls_never_rate_limited(client_factory, auth_headers):
    """Calling /usage does not record hits and never returns 429 even when rate_limit=1."""
    client = client_factory(rate_limit=1)

    # Multiple /usage calls don't exceed rate limit
    for _ in range(5):
        resp = client.get("/usage", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["requests_last_minute"] == 0

    # Exhaust rate limit using /ask
    ask_resp1 = client.post(
        "/ask", json={"question": "Help me"}, headers=auth_headers
    )
    assert ask_resp1.status_code == 200

    # /ask is now blocked with 429
    ask_resp2 = client.post(
        "/ask", json={"question": "Help again"}, headers=auth_headers
    )
    assert ask_resp2.status_code == 429

    # /usage still returns 200 despite /ask being blocked
    for _ in range(5):
        resp = client.get("/usage", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["requests_last_minute"] == 1


def test_health_reports_customer_support_service(client):
    """Health check reports service as 'customer-support-agent'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "customer-support-agent"


def test_fastapi_title():
    """FastAPI application title is 'Customer Support Agent'."""
    from app.main import app

    assert app.title == "Customer Support Agent"
