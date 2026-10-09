"""Command-line interface for analyzing a saved unified diff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from patchpilot.analyzer import analyze
from patchpilot.models import AnalyzeRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patchpilot",
        description="Explainable static risk triage for a unified diff.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    command = subparsers.add_parser("analyze", help="Analyze a diff file or standard input.")
    command.add_argument(
        "--diff-file",
        type=Path,
        help="Path to a unified diff. If omitted, read standard input.",
    )
    command.add_argument("--title", default="Local diff analysis")
    command.add_argument("--base-ref", default="base")
    command.add_argument("--head-ref", default="head")
    command.add_argument("--json", action="store_true", help="Print the full JSON response.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        diff = args.diff_file.read_text(encoding="utf-8") if args.diff_file else sys.stdin.read()
        request = AnalyzeRequest(
            title=args.title,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            diff=diff,
        )
        result = analyze(request)
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"patchpilot: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(result.model_dump_json(indent=2))
        return 0

    print(f"{result.title}: {result.risk_level.upper()} risk ({result.risk_score}/100)")
    print(result.summary)
    print()
    if result.files:
        print("Changed files:")
        for item in result.files:
            print(f"  {item.path} (+{item.additions}/-{item.deletions})")
        print()
    print("Findings:")
    for finding in result.findings:
        print(f"  [{finding.severity.upper()}] {finding.title} ({finding.rule_id})")
        print(f"    {finding.detail}")
        for evidence in finding.evidence:
            print(f"    Evidence: {evidence}")
    print()
    print("Suggested checks:")
    for recommendation in result.recommended_tests:
        print(f"  - {recommendation}")
    print()
    print(result.disclaimer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
