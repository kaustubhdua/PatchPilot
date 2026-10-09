from fastapi.testclient import TestClient

from patchpilot.api import InMemoryRateLimiter, app

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
