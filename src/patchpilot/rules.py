"""Deterministic, explainable heuristics for changed-file risk triage."""

from __future__ import annotations

import re

from patchpilot.models import FileChange, Finding
from patchpilot.parser import ParsedFile

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


def is_test_path(path: str) -> bool:
    low = path.lower().replace("\\", "/")
    name = low.rsplit("/", 1)[-1]
    return (
        "/tests/" in f"/{low}/"
        or low.startswith(("tests/", "test/"))
        or name.startswith(("test_", "tests."))
        or ".test." in name
        or ".spec." in name
    )


def _is_sensitive_path(path: str) -> bool:
    return any(term in path.lower() for term in SENSITIVE)


def _finding(
    rule_id: str,
    severity: str,
    title: str,
    detail: str,
    evidence: list[str],
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        title=title,
        detail=detail,
        evidence=evidence[:5],
    )


def evaluate_risk(
    parsed: list[ParsedFile],
    changes: list[FileChange],
) -> tuple[int, list[Finding]]:
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
        findings.append(_finding(rule, severity, title, detail, evidence))

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

    additions = sum(item.additions for item in changes)
    deletions = sum(item.deletions for item in changes)
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
    if not findings:
        findings.append(
            _finding(
                "no-static-signals",
                "info",
                "No configured risk signals detected",
                "Absence of these signals does not prove safety.",
                [f"{len(changes)} files inspected"],
            )
        )
    return score, findings
