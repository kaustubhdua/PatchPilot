from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="PatchPilot API",
    description="Explainable pull-request risk analysis",
    version="0.1.0",
)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "patchpilot"}


@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze_diff(payload: AnalyzeRequest) -> AnalyzeResponse:
    return analyze(payload)


@app.exception_handler(ValidationError)
async def validation_error_handler(_request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
