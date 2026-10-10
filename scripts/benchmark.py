"""Run a small rule-ID benchmark against benchmarks/cases.jsonl.

This starter corpus is for reproducibility and regression, not a claim of
production detection quality. Run: python scripts/benchmark.py
"""
from __future__ import annotations

import json
from pathlib import Path

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks" / "cases.jsonl"


def main() -> int:
    cases = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line]
    counts = {rule: {"tp": 0, "fp": 0, "fn": 0} for case in cases for rule in case["expected_rule_ids"]}
    all_rules = set(counts)
    rows = []
    for case in cases:
        result = analyze(AnalyzeRequest(title=case["id"], diff=case["diff"]))
        actual = {finding.rule_id for finding in result.findings}
        expected = set(case["expected_rule_ids"])
        all_rules.update(actual)
        rows.append((case["id"], sorted(expected), sorted(actual)))
        for rule in all_rules:
            stats = counts.setdefault(rule, {"tp": 0, "fp": 0, "fn": 0})
            if rule in expected and rule in actual:
                stats["tp"] += 1
            elif rule in actual and rule not in expected:
                stats["fp"] += 1
            elif rule in expected and rule not in actual:
                stats["fn"] += 1
    print(f"Dataset: {DATASET.relative_to(ROOT)} ({len(cases)} cases)")
    for case_id, expected, actual in rows:
        print(f"- {case_id}: expected={expected} actual={actual}")
    print("\nPer-rule metrics (tiny starter corpus; not production evidence):")
    for rule, values in sorted(counts.items()):
        tp, fp, fn = values["tp"], values["fp"], values["fn"]
        precision = f"{tp / (tp + fp):.3f}" if tp + fp else "n/a"
        recall = f"{tp / (tp + fn):.3f}" if tp + fn else "n/a"
        print(f"{rule}: TP={tp} FP={fp} FN={fn} precision={precision} recall={recall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
