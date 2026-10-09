"""Safe operational endpoints and bounded analysis API for PatchPilot."""

from __future__ import annotations

import logging
import time
from collections import deque
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger("patchpilot.api")

app = FastAPI(
    title="PatchPilot API",
    description="Explainable pull-request risk analysis",
    version="0.2.0",
)


class InMemoryRateLimiter:
    """Per-process sliding-window limiter; use a shared gateway with multiple workers."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(timestamp)
            # Avoid unbounded growth from one-off client addresses.
            if len(self._hits) > 10_000:
                expired = [
                    item
                    for item, values in self._hits.items()
                    if not values or values[-1] <= cutoff
                ]
                for item in expired[:5_000]:
                    self._hits.pop(item, None)
            return True


rate_limiter = InMemoryRateLimiter()


@app.middleware("http")
async def protect_analysis_endpoint(request: Request, call_next):
    if request.url.path == "/v1/analyze" and request.method == "POST":
        # Do not trust X-Forwarded-For here; only honor proxy headers after
        # configuring a trusted proxy chain at the ASGI server.
        client = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client):
            return JSONResponse(
                status_code=429,
                content={"detail": "Analysis rate limit exceeded. Retry shortly."},
                headers={"Retry-After": "60"},
            )
    return await call_next(request)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "patchpilot"}


@app.get("/ready", tags=["operations"])
def ready() -> dict[str, str]:
    """Readiness probe for the stateless MVP."""
    return {"status": "ready", "service": "patchpilot"}


@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze_diff(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze(payload)
    except Exception:
        # Avoid returning source snippets or internals in unexpected error responses.
        logger.exception("Unexpected analysis failure")
        return JSONResponse(
            status_code=500,
            content={"detail": "Analysis failed unexpectedly. Check server logs."},
        )


@app.exception_handler(ValidationError)
async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
