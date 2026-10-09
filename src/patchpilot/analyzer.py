from __future__ import annotations

import re
from dataclasses import dataclass

from patchpilot.models import AnalyzeRequest, AnalyzeResponse, FileChange, Finding

HEADER = re.compile(r"^diff --git a/(.*) b/(.*)$")
SENSITIVE = ("auth", "permission", "policy", "crypto", "secret", "session", "login", "security")
DEPENDENCIES = (
    "requirements",
    "pyproject.toml",
    "poetry.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
    "go.sum",
)
RISKY_PATTERNS = (
    (
        re.compile(r"\beval\s*\("),
        "dynamic-evaluation",
        "Dynamic evaluation pattern",
        "Check whether untrusted input can reach eval().",
    ),
    (
        re.compile(r"\bshell\s*=\s*true\b", re.I),
        "shell-execution",
        "Shell execution enabled",
        "Review command construction and input handling.",
    ),
    (
        re.compile(r"\bverify\s*=\s*false\b", re.I),
        "tls-verification-disabled",
        "TLS verification disabled",
        "Do not disable certificate checks in production.",
    ),
)


@dataclass
class _ParsedFile:
    path: str
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] | None = None
    binary: bool = False

    def __post_init__(self) -> None:
        if self.added_lines is None:
            self.added_lines = []


def _parse_diff(diff: str) -> list[_ParsedFile]:
    """Parse file boundaries and line counts without interpreting file contents as headers."""
    files: list[_ParsedFile] = []
    current: _ParsedFile | None = None
    in_hunk = False

    for line in diff.splitlines():
        match = HEADER.match(line)
        if match:
            current = _ParsedFile(path=match.group(2))
            files.append(current)
            in_hunk = False
            continue
        if current is None:
            continue
        if line.startswith(("rename to ", "+++ b/")):
            if line.startswith("rename to "):
                current.path = line.removeprefix("rename to ")
            elif line != "+++ b/":
                current.path = line.removeprefix("+++ b/")
            in_hunk = False
            continue
        if line.startswith("Binary files ") or line == "GIT binary patch":
            current.binary = True
            in_hunk = False
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
        elif line.startswith("\\ No newline"):
            continue
    return files


def _is_sensitive_path(path: str) -> bool:
    return any(term in path.lower() for term in SENSITIVE)


def _is_test_path(path: str) -> bool:
    low = path.lower().replace("\\", "/")
    name = low.rsplit("/", 1)[-1]
    return (
        "/tests/" in f"/{low}/"
        or low.startswith(("tests/", "test/"))
        or name.startswith(("test_", "tests."))
        or ".test." in name
        or ".spec." in name
    )


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    parsed = _parse_diff(request.diff)
    changes = [
        FileChange(
            path=item.path,
            additions=item.additions,
            deletions=item.deletions,
            is_test=_is_test_path(item.path),
        )
        for item in parsed
    ]
    additions = sum(item.additions for item in changes)
    deletions = sum(item.deletions for item in changes)
    findings: list[Finding] = []
    score = 0

    def add(
        rule: str,
        severity: str,
        points: int,
        title: str,
        detail: str,
        evidence: list[str],
    ) -> None:
        nonlocal score
        score += points
        findings.append(
            Finding(
                rule_id=rule,
                severity=severity,
                title=title,
                detail=detail,
                evidence=evidence[:5],
            )
        )

    sensitive = [item.path for item in changes if _is_sensitive_path(item.path)]
    if sensitive:
        add(
            "sensitive-path",
            "high",
            20,
            "Sensitive code path changed",
            "Review authentication and security-sensitive behavior.",
            sensitive,
        )

    dependencies = [
        item.path for item in changes if any(term in item.path.lower() for term in DEPENDENCIES)
    ]
    if dependencies:
        add(
            "dependency-change",
            "medium",
            12,
            "Dependency manifest changed",
            "Review version changes, lockfile consistency and known advisories.",
            dependencies,
        )

    if len(changes) >= 5:
        add(
            "broad-change",
            "medium",
            10,
            "Broad change set",
            "Review interactions between modified files.",
            [f"{len(changes)} files changed"],
        )
    if additions + deletions >= 200:
        add(
            "large-diff",
            "medium",
            12,
            "Large diff",
            "Consider splitting unrelated changes.",
            [f"{additions} additions", f"{deletions} deletions"],
        )

    added_text = "\n".join(line for item in parsed for line in item.added_lines)
    for pattern, rule, title, detail in RISKY_PATTERNS:
        matches = [line.strip() for line in added_text.splitlines() if pattern.search(line)]
        if matches:
            add(rule, "high", 18, title, detail, matches)

    production = [
        item
        for item in changes
        if not item.is_test and not item.path.lower().endswith((".md", ".txt", ".rst"))
    ]
    if production and not any(item.is_test for item in changes):
        add(
            "no-test-files",
            "medium",
            12,
            "No test files changed",
            "Confirm tests cover the changed production behavior.",
            [item.path for item in production[:5]],
        )

    score = min(score, 100)
    if score < 25:
        level = "low"
    elif score < 50:
        level = "medium"
    elif score < 75:
        level = "high"
    else:
        level = "critical"
    if not findings:
        findings.append(
            Finding(
                rule_id="no-static-signals",
                severity="info",
                title="No configured risk signals detected",
                detail="Absence of these signals does not prove safety.",
                evidence=[f"{len(changes)} files inspected"],
            )
        )

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
