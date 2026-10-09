from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest

def test_risky_pattern_has_evidence():
    result = analyze(AnalyzeRequest(diff="diff --git a/runner.py b/runner.py\n+eval(user_input)"))
    assert result.risk_score > 0
    assert any("risky-pattern" in f.rule_id for f in result.findings)
    assert result.findings[0].evidence

def test_empty_file_list_stays_low_and_explains_limit():
    result = analyze(AnalyzeRequest(diff="+some text without a git file header"))
    assert result.files_changed == 0
    assert result.risk_level == "low"
    assert result.disclaimer
