import io
import json

from patchpilot.cli import main


def test_cli_reads_diff_from_stdin_and_prints_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -0,0 +1 @@
+safe()
"""
        ),
    )
    assert main(["analyze", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["files_changed"] == 1
    assert output["files"][0]["path"] == "app.py"


def test_cli_returns_error_for_missing_diff_file(capsys, tmp_path):
    missing = tmp_path / "missing.diff"
    assert main(["analyze", "--diff-file", str(missing)]) == 2
    assert "patchpilot:" in capsys.readouterr().err


def test_cli_displays_incomplete_diff_warning(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
-old()
+new()
"""
        ),
    )
    assert main(["analyze"]) == 0
    output = capsys.readouterr().out
    assert "Analysis warnings:" in output
    assert "app.py" in output
    assert "partial" in output


def test_cli_displays_risky_finding_location(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            """diff --git a/src/runner.py b/src/runner.py
--- a/src/runner.py
+++ b/src/runner.py
@@ -1 +1 @@
+eval(user_input)
"""
        ),
    )
    assert main(["analyze"]) == 0
    output = capsys.readouterr().out
    assert "Location: src/runner.py:1" in output
