from fastapi import FastAPI
from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="PatchPilot API", description="Explainable pull-request risk analysis", version="0.1.0")

@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "patchpilot"}

@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze_diff(payload: AnalyzeRequest) -> AnalyzeResponse:
    return analyze(payload)
