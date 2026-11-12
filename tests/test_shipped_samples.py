"""The diffs and request bodies we ship in docs and the web UI must parse cleanly."""

import json
import re
from pathlib import Path

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest

ROOT = Path(__file__).resolve().parent.parent


def run(diff: str):
    return analyze(AnalyzeRequest(diff=diff))


def test_cli_walkthrough_example_diff_is_well_formed():
    result = run((ROOT / "examples" / "tls-verification-change.diff").read_text(encoding="utf-8"))
    assert result.analysis_complete
    assert not result.analysis_warnings
    assert "tls-verification-disabled" in {f.rule_id for f in result.findings}


def test_web_workbench_sample_diff_is_well_formed():
    source = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
    match = re.search(r"const SAMPLE_DIFF = `(.*?)`;", source, re.S)
    assert match, "SAMPLE_DIFF not found in website/app.js"
    result = run(match.group(1))
    assert result.analysis_complete
    assert not result.analysis_warnings
    assert "sensitive-path" in {f.rule_id for f in result.findings}


def test_readme_api_example_decodes_to_a_multiline_diff():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"~~~json\n(\{.*?\})\n~~~", readme, re.S)
    assert match, "API example not found in README.md"
    body = json.loads(match.group(1))
    assert "\n" in body["diff"], "README example must use single-backslash \\n escapes"
    result = run(body["diff"])
    assert result.analysis_complete
    assert [(f.path, f.additions, f.deletions) for f in result.files] == [("src/example.py", 1, 1)]
