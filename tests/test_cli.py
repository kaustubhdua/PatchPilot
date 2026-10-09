import io
import json

from patchpilot.cli import main


def test_cli_reads_diff_from_stdin_and_prints_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n+safe()\n"
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
