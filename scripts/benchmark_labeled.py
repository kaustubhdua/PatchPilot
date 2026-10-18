"""Measure heuristic-rule and test-suggestion quality on a reviewer-labelled synthetic corpus.

Run from the repository root:
    python scripts/benchmark_labeled.py

The outputs describe this tiny synthetic fixture set only, not production accuracy.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks" / "triage-labeled-v1.jsonl"
TEST_LABELS = {"pytest", "js-quality", "generic", "regression"}


def classify_test_suggestions(suggestions: list[str]) -> set[str]:
    labels: set[str] = set()
    for suggestion in suggestions:
        low = suggestion.lower()
        if "relevant pytest tests" in low:
            labels.add("pytest")
        if "unit tests, type checks and lint" in low:
            labels.add("js-quality")
        if "relevant test suite" in low:
            labels.add("generic")
        if "add focused regression tests" in low:
            labels.add("regression")
    return labels


def score(expected_rows: list[set[str]], actual_rows: list[set[str]]) -> dict[str, Any]:
    tp = fp = fn = 0
    for expected, actual in zip(expected_rows, actual_rows, strict=True):
        tp += len(expected & actual)
        fp += len(actual - expected)
        fn += len(expected - actual)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def render(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> int:
    cases = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise SystemExit(f"No cases found in {DATASET}")
    required = {"id", "diff", "expected_rule_ids", "expected_test_suggestions", "notes"}
    seen: set[str] = set()
    rule_expected: list[set[str]] = []
    rule_actual: list[set[str]] = []
    test_expected: list[set[str]] = []
    test_actual: list[set[str]] = []
    started = time.perf_counter()

    for case in cases:
        missing = required - case.keys()
        if missing:
            raise SystemExit(f"{case.get('id', '<unknown>')}: missing fields {sorted(missing)}")
        case_id = case["id"]
        if case_id in seen:
            raise SystemExit(f"Duplicate case id: {case_id}")
        seen.add(case_id)

        expected_rules = set(case["expected_rule_ids"])
        # no-static-signals is an informational fallback, not a risk-rule prediction.
        result = analyze(AnalyzeRequest(title=case_id, diff=case["diff"]))
        actual_rules = {
            finding.rule_id for finding in result.findings if finding.rule_id != "no-static-signals"
        }
        expected_tests = set(case["expected_test_suggestions"])
        unknown_tests = expected_tests - TEST_LABELS
        if unknown_tests:
            raise SystemExit(f"{case_id}: unknown test labels {sorted(unknown_tests)}")
        actual_tests = classify_test_suggestions(result.recommended_tests)

        rule_expected.append(expected_rules)
        rule_actual.append(actual_rules)
        test_expected.append(expected_tests)
        test_actual.append(actual_tests)

        # Per-case comparison is the primary result; aggregate metrics follow below.
        print(
            f"{case_id}: "
            f"rules expected={sorted(expected_rules)} actual={sorted(actual_rules)}; "
            f"tests expected={sorted(expected_tests)} actual={sorted(actual_tests)}"
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    rule_metrics = score(rule_expected, rule_actual)
    test_metrics = score(test_expected, test_actual)
    exact_rule_cases = sum(e == a for e, a in zip(rule_expected, rule_actual, strict=True))
    exact_test_cases = sum(e == a for e, a in zip(test_expected, test_actual, strict=True))

    print(f"\nCorpus: {DATASET.relative_to(ROOT)}")
    print(f"Cases: {len(cases)} (synthetic, manually labelled)")
    print(f"Elapsed: {elapsed_ms:.2f} ms (local process time; not service/API latency)")
    print(
        "Risk-rule micro metrics: "
        f"TP={rule_metrics['tp']} FP={rule_metrics['fp']} FN={rule_metrics['fn']} "
        f"precision={render(rule_metrics['precision'])} "
        f"recall={render(rule_metrics['recall'])} F1={render(rule_metrics['f1'])}"
    )
    print(
        "Test-suggestion micro metrics: "
        f"TP={test_metrics['tp']} FP={test_metrics['fp']} FN={test_metrics['fn']} "
        f"precision/relevance={render(test_metrics['precision'])} "
        f"recall={render(test_metrics['recall'])} F1={render(test_metrics['f1'])}"
    )
    print(
        "Exact-set agreement: "
        f"rules={exact_rule_cases}/{len(cases)} "
        f"({exact_rule_cases / len(cases):.1%}); "
        f"test suggestions={exact_test_cases}/{len(cases)} "
        f"({exact_test_cases / len(cases):.1%})"
    )
    print(
        "Caution: these metrics measure only synthetic hand-labelled fixtures and label policy. "
        "They are not estimates of performance on real pull requests or security defects."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
