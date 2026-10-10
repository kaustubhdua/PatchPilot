# Architecture

PatchPilot is a deterministic diff-triage service. The MVP accepts unified diff text, parses file sections and hunk lines, evaluates conservative static rules, and returns a structured response.

## Request path

1. FastAPI validates an `AnalyzeRequest` with a bounded diff.
2. `parser.py` extracts file metadata, changed-line counts and added lines.
3. `analyzer.py` builds file summaries and invokes deterministic rules.
4. `rules.py` produces findings and a heuristic score.
5. The API or CLI serializes the result.

## Trust boundaries

- A diff is untrusted data. It is never executed, cloned, installed, or passed to a shell.
- Added source text can contain secrets. Deployments must define access controls, logging policy and retention.
- Pattern matches are signals for human review, not proof of a vulnerability.
- A malformed or incomplete diff may lead to incomplete results. Do not treat an empty finding list as proof of safety.

## Current limitations

- Rules use text and path heuristics; the engine does not understand program semantics.
- Test recommendations are based on changed file extensions and presence of test paths.
- The in-memory rate limiter is per process and is not a distributed quota.
- The parser is intentionally lightweight and is not a complete implementation of every Git diff extension.
- No GitHub App, persistent history, dashboard, LLM integration, or code execution is part of the current MVP.

## Extension guidance

Keep parsing, rule detection, scoring and recommendations independently testable. Give each rule a stable identifier and add both positive and negative examples. Add language-aware parsers only when their accuracy can be measured against a labeled corpus.
