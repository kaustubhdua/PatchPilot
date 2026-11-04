import asyncio

import pytest
from fastapi.testclient import TestClient

import patchpilot.api as api
from patchpilot.api import (
    MAX_ANALYZE_BODY_BYTES,
    AnalyzeBodyLimitMiddleware,
    InMemoryRateLimiter,
    app,
    parse_cors_origins,
)

client = TestClient(app)


def test_health_and_readiness():
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "patchpilot"}


def test_analyze_sensitive_diff():
    diff = (
        "diff --git a/src/auth.py b/src/auth.py\n"
        "--- a/src/auth.py\n+++ b/src/auth.py\n"
        "@@ -1 +1,2 @@\n+def authenticate(token):\n+    return True\n"
    )
    response = client.post("/v1/analyze", json={"title": "Auth update", "diff": diff})
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] > 0
    assert any(f["rule_id"] == "sensitive-path" for f in body["findings"])
    assert body["recommended_tests"]


def test_validates_diff_size_and_extra_fields():
    assert client.post("/v1/analyze", json={"diff": ""}).status_code == 422
    assert client.post("/v1/analyze", json={"diff": "+ok", "unexpected": True}).status_code == 422
    assert client.post("/v1/analyze", json={"diff": "+" + "x" * 500001}).status_code == 422


def test_rate_limiter_enforces_window_and_expires_old_hits():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("client-a", now=100)
    assert limiter.allow("client-a", now=101)
    assert not limiter.allow("client-a", now=102)
    assert limiter.allow("client-a", now=111)


def test_rate_limit_isolated_by_client():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10)
    assert limiter.allow("client-a", now=100)
    assert not limiter.allow("client-a", now=101)
    assert limiter.allow("client-b", now=101)


def test_analysis_endpoint_returns_429_after_configured_limit(monkeypatch):
    monkeypatch.setattr(api, "rate_limiter", InMemoryRateLimiter(limit=1, window_seconds=60))
    payload = {"diff": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -0,0 +1 @@\n+safe()\n"}
    first = client.post("/v1/analyze", json=payload)
    second = client.post("/v1/analyze", json=payload)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"


def test_cors_origins_are_exact_normalized_and_deduplicated():
    assert parse_cors_origins(
        " https://Example.com/,http://localhost:3000,https://example.com "
    ) == ["https://example.com", "http://localhost:3000"]


def test_cors_origins_remove_default_ports():
    assert parse_cors_origins("https://example.com:443,http://localhost:80") == [
        "https://example.com",
        "http://localhost",
    ]


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "https://example.com/path",
        "javascript://example.com",
        "https://user:password@example.com",
        "https://example.com?query=1",
        "https://example.com:invalid",
    ],
)
def test_cors_origins_reject_unsafe_or_malformed_values(value):
    with pytest.raises(ValueError):
        parse_cors_origins(value)


def test_website_is_served_from_api_origin():
    home = client.get("/")
    assert home.status_code == 200
    assert "PatchPilot" in home.text
    stylesheet = client.get("/styles.css")
    assert stylesheet.status_code == 200
    assert "--bg:" in stylesheet.text


def test_analysis_endpoint_rejects_oversized_declared_body():
    body = b"x" * (MAX_ANALYZE_BODY_BYTES + 1)
    response = client.post(
        "/v1/analyze",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert "byte limit" in response.json()["detail"]


def test_streamed_analysis_body_limit_without_content_length():
    messages = [
        {"type": "http.request", "body": b"1234", "more_body": True},
        {"type": "http.request", "body": b"5678", "more_body": False},
    ]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "http.request" and not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/analyze",
        "headers": [],
    }
    middleware = AnalyzeBodyLimitMiddleware(downstream, max_bytes=5)
    asyncio.run(middleware(scope, receive, send))
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
