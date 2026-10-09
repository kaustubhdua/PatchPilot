import re
from patchpilot.models import AnalyzeRequest, AnalyzeResponse, FileChange, Finding

HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
SENSITIVE = ("auth", "permission", "policy", "crypto", "secret", "session", "login", "security")
DEPENDENCIES = ("requirements", "pyproject.toml", "poetry.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "cargo.lock", "go.sum")

def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    files = []
    current = None
    for line in request.diff.splitlines():
        match = HEADER.match(line)
        if match:
            current = {"path": match.group(2), "additions": 0, "deletions": 0}
            files.append(current)
        elif current is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current["additions"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                current["deletions"] += 1

    changes = []
    findings = []
    score = 0
    for item in files:
        path = item["path"]
        low = path.lower()
        name = low.rsplit("/", 1)[-1]
        is_test = ("/tests/" in f"/{low}/" or low.startswith("tests/") or
                   name.startswith("test_") or ".test." in name or ".spec." in name)
        changes.append(FileChange(**item, is_test=is_test))
    additions = sum(f.additions for f in changes)
    deletions = sum(f.deletions for f in changes)

    def add(rule, severity, points, title, detail, evidence):
        nonlocal score
        score += points
        findings.append(Finding(rule_id=rule, severity=severity, title=title,
                                detail=detail, evidence=evidence[:5]))

    sensitive = [f.path for f in changes if any(t in f.path.lower() for t in SENSITIVE)]
    if sensitive:
        add("sensitive-path", "high", 20, "Sensitive code path changed",
            "Review authentication and security-sensitive behavior.", sensitive)
    deps = [f.path for f in changes if any(t in f.path.lower() for t in DEPENDENCIES)]
    if deps:
        add("dependency-change", "medium", 12, "Dependency manifest changed",
            "Review version changes and known advisories.", deps)
    if len(changes) >= 5:
        add("broad-change", "medium", 10, "Broad change set",
            "Review interactions between modified files.", [f"{len(changes)} files changed"])
    if additions + deletions >= 200:
        add("large-diff", "medium", 12, "Large diff",
            "Consider splitting unrelated changes.", [f"{additions} additions", f"{deletions} deletions"])
    for token, title, detail in [
        ("eval(", "Dynamic evaluation pattern", "Check whether untrusted input can reach eval()."),
        ("shell=true", "Shell execution enabled", "Review command construction and input handling."),
        ("verify=false", "TLS verification disabled", "Do not disable certificate checks in production."),
    ]:
        if token in request.diff.lower():
            add("risky-pattern-" + token.replace("(", "").replace("=", "-"),
                "high", 18, title, detail, [f"Diff contains {token!r}"])
    production = [f for f in changes if not f.is_test and not f.path.lower().endswith((".md", ".txt", ".rst"))]
    if production and not any(f.is_test for f in changes):
        add("no-test-files", "medium", 12, "No test files changed",
            "Confirm tests cover the changed production behavior.", [f.path for f in production[:5]])
    score = min(score, 100)
    level = "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
    if not findings:
        findings.append(Finding(rule_id="no-static-signals", severity="info",
            title="No configured risk signals detected",
            detail="Absence of these signals does not prove safety.",
            evidence=[f"{len(changes)} files inspected"]))
    extensions = {f.path.rsplit(".", 1)[-1].lower() for f in changes if "." in f.path}
    recommendations = []
    if "py" in extensions:
        recommendations.append("Run relevant pytest tests and add regression coverage.")
    if extensions & {"ts", "tsx", "js", "jsx"}:
        recommendations.append("Run unit tests, type checks and lint.")
    if not recommendations:
        recommendations.append("Run the relevant test suite and inspect uncovered edge cases.")
    if changes and not any(f.is_test for f in changes):
        recommendations.append("Add focused regression tests for changed behavior.")
    return AnalyzeResponse(title=request.title, base_ref=request.base_ref, head_ref=request.head_ref,
        risk_score=score, risk_level=level,
        summary=f"Inspected {len(changes)} file(s), {additions} additions and {deletions} deletions. Score uses static heuristics.",
        files_changed=len(changes), additions=additions, deletions=deletions, files=changes,
        findings=findings, recommended_tests=recommendations,
        disclaimer="Heuristic triage only; not a defect probability, security audit or merge recommendation.")
