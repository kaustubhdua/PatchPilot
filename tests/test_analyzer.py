from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest


def run(diff: str):
    return analyze(AnalyzeRequest(diff=diff))


def test_risky_pattern_only_matches_added_lines():
    diff = (
        "diff --git a/runner.py b/runner.py\n"
        "--- a/runner.py\n+++ b/runner.py\n@@ -1 +1 @@\n"
        "-eval(old_input)\n+safe_call(user_input)\n"
    )
    result = run(diff)
    assert not any(f.rule_id == "dynamic-evaluation" for f in result.findings)


def test_added_risky_pattern_has_line_evidence():
    diff = (
        "diff --git a/runner.py b/runner.py\n"
        "--- a/runner.py\n+++ b/runner.py\n@@ -1 +1 @@\n"
        "-safe_call()\n+eval(user_input)\n"
    )
    result = run(diff)
    finding = next(f for f in result.findings if f.rule_id == "dynamic-evaluation")
    assert "eval(user_input)" in finding.evidence
    assert finding.severity == "high"


def test_counts_only_hunk_lines_and_ignores_headers():
    diff = (
        "diff --git a/a.py b/a.py\n"
        "index abc..def 100644\n"
        "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n"
        "-old()\n+new()\n context()\n"
    )
    result = run(diff)
    assert result.files_changed == 1
    assert result.additions == 1
    assert result.deletions == 1


def test_multiple_files_and_test_detection():
    diff = (
        "diff --git a/src/app.py b/src/app.py\n"
        "--- a/src/app.py\n+++ b/src/app.py\n@@ -0,0 +1 @@\n+run()\n"
        "diff --git a/tests/test_app.py b/tests/test_app.py\n"
        "--- a/tests/test_app.py\n+++ b/tests/test_app.py\n@@ -0,0 +1 @@\n"
        "+def test_run(): pass\n"
    )
    result = run(diff)
    assert result.files_changed == 2
    assert [f.is_test for f in result.files] == [False, True]
    assert not any(f.rule_id == "no-test-files" for f in result.findings)


def test_binary_file_is_counted_without_fake_line_counts():
    diff = (
        "diff --git a/image.png b/image.png\n"
        "Binary files a/image.png and b/image.png differ\n"
    )
    result = run(diff)
    assert result.files_changed == 1
    assert result.additions == 0
    assert result.deletions == 0


def test_empty_file_list_stays_low_and_explains_limit():
    result = run("+some text without a git file header")
    assert result.files_changed == 0
    assert result.risk_level == "low"
    assert result.disclaimer


def test_sensitive_path_and_dependency_rules():
    diff = (
        "diff --git a/src/auth.py b/src/auth.py\n"
        "--- a/src/auth.py\n+++ b/src/auth.py\n@@ -0,0 +1 @@\n+authenticate()\n"
        "diff --git a/requirements.txt b/requirements.txt\n"
        "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -1 +1 @@\n+safe-package==1.0\n"
    )
    result = run(diff)
    rules = {finding.rule_id for finding in result.findings}
    assert "sensitive-path" in rules
    assert "dependency-change" in rules
