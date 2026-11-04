"""Safe operational endpoints and bounded analysis API for PatchPilot."""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger("patchpilot.api")

app = FastAPI(
    title="PatchPilot API",
    description="Explainable pull-request risk analysis",
    version="0.2.0",
)


def parse_cors_origins(value: str) -> list[str]:
    """Parse exact HTTP(S) origins and reject wildcard or malformed entries."""
    origins: list[str] = []
    for raw_origin in value.split(","):
        origin = raw_origin.strip()
        if not origin:
            continue
        if origin == "*":
            raise ValueError("PATCHPILOT_CORS_ORIGINS must not contain wildcard origins.")
        try:
            parsed = urlsplit(origin)
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("PATCHPILOT_CORS_ORIGINS contains an invalid origin.") from exc
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "PATCHPILOT_CORS_ORIGINS entries must be exact HTTP(S) origins "
                "without credentials, paths, query strings, or fragments."
            )
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower()
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        port = parsed.port
        default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        netloc = hostname if port is None or default_port else f"{hostname}:{port}"
        normalized = f"{scheme}://{netloc}"
        if normalized not in origins:
            origins.append(normalized)
    return origins





MAX_ANALYZE_BODY_BYTES = 4_000_000


class _RequestBodyTooLarge(Exception):
    """Raised when a streamed analysis request exceeds its byte budget."""


class AnalyzeBodyLimitMiddleware:
    """Bound analysis request bytes before JSON parsing or Pydantic validation."""

    def __init__(self, app, max_bytes: int = MAX_ANALYZE_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("path") != "/v1/analyze"
            or scope.get("method") != "POST"
        ):
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                content_length = int(raw_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
                await response(scope, receive, send)
                return
            if content_length < 0:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
                await response(scope, receive, send)
                return
            if content_length > self.max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Analysis request body exceeds the byte limit."},
                )
                await response(scope, receive, send)
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Analysis request body exceeds the byte limit."},
            )
            await response(scope, receive, send)


# Configure exact trusted website origins at deployment time; do not use wildcard
# origins for a public API. Invalid configuration fails at startup.
_cors_origins = parse_cors_origins(os.getenv("PATCHPILOT_CORS_ORIGINS", ""))
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

# Bound both declared and streamed bodies before FastAPI parses the JSON payload.
app.add_middleware(AnalyzeBodyLimitMiddleware)


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


# Serve the web workbench from the same origin when the static site is available.
# In containers PATCHPILOT_WEB_DIR points to /app/website; local source defaults
# to the repository's website directory. API routes above take precedence.
_default_web_dir = Path(__file__).resolve().parents[2] / "website"
_web_dir = Path(os.getenv("PATCHPILOT_WEB_DIR", str(_default_web_dir)))
if _web_dir.is_dir() and (_web_dir / "index.html").is_file():
    app.mount("/", StaticFiles(directory=_web_dir, html=True), name="website")
