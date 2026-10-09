"""Public orchestration for PatchPilot's deterministic analyzer."""

from __future__ import annotations

from patchpilot.models import AnalyzeRequest, AnalyzeResponse, FileChange
from patchpilot.parser import parse_unified_diff
from patchpilot.rules import evaluate_risk, is_test_path


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    parsed = parse_unified_diff(request.diff)
    changes = [
        FileChange(
            path=item.path,
            additions=item.additions,
            deletions=item.deletions,
            is_test=is_test_path(item.path),
        )
        for item in parsed
    ]
    additions = sum(item.additions for item in changes)
    deletions = sum(item.deletions for item in changes)
    score, findings = evaluate_risk(parsed, changes)

    if score < 25:
        level = "low"
    elif score < 50:
        level = "medium"
    elif score < 75:
        level = "high"
    else:
        level = "critical"

    extensions = {item.path.rsplit(".", 1)[-1].lower() for item in changes if "." in item.path}
    recommendations = []
    if "py" in extensions:
        recommendations.append("Run relevant pytest tests and add regression coverage.")
    if extensions & {"ts", "tsx", "js", "jsx"}:
        recommendations.append("Run unit tests, type checks and lint.")
    if not recommendations:
        recommendations.append("Run the relevant test suite and inspect uncovered edge cases.")
    if changes and not any(item.is_test for item in changes):
        recommendations.append("Add focused regression tests for changed behavior.")

    return AnalyzeResponse(
        title=request.title,
        base_ref=request.base_ref,
        head_ref=request.head_ref,
        risk_score=score,
        risk_level=level,
        summary=(
            f"Inspected {len(changes)} file(s), {additions} additions and "
            f"{deletions} deletions. Score uses static heuristics."
        ),
        files_changed=len(changes),
        additions=additions,
        deletions=deletions,
        files=changes,
        findings=findings,
        recommended_tests=recommendations,
        disclaimer=(
            "Heuristic triage only; not a defect probability, security audit "
            "or merge recommendation."
        ),
    )
