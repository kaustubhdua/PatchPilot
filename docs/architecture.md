# Architecture

PatchPilot is a deterministic diff-triage service. The MVP accepts unified diff text, parses file sections and hunk lines, evaluates conservative static rules, and returns a structured response.

## Request path

1. FastAPI validates an `AnalyzeRequest` with a bounded diff.
2. `parser.py` extracts file metadata, changed-line counts, added lines, and malformed/incomplete hunk counts.
3. `analyzer.py` builds file summaries, surfaces parser-integrity warnings, and invokes deterministic rules.
4. `rules.py` produces findings, preserves matched source text as evidence, attaches file/new-line locations for risky added-line patterns, and calculates a heuristic score.
5. The API or CLI serializes the result; the web workbench displays warnings alongside the summary.

## Analysis integrity

- A hunk is counted only while its declared old/new line ranges permit it.
- Hunk overruns, malformed headers, and incomplete ranges are recorded per file.
- The response includes `malformed_hunks` for each file and an `analysis_warnings` list.
- The response exposes `analysis_complete`; any malformed or incomplete hunk makes it `false`, so consumers cannot mistake a partial low score for a complete review.
- Partial counts are not silently presented as complete: users are warned that findings and statistics may omit changes.
- Warnings do not attempt to repair or infer missing patch content.
- Risky added-line findings expose source locations separately from evidence text, preserving the evidence field for existing consumers.

## Trust boundaries

- A diff is untrusted data. It is never executed, cloned, installed, or passed to a shell.
- Added source text can contain secrets. Deployments must define access controls, logging policy and retention.
- Pattern matches are signals for human review, not proof of a vulnerability.
- A malformed or incomplete diff may lead to incomplete results. Do not treat an empty finding list as proof of safety.

## Current limitations

- Rules use text and path heuristics; the engine does not understand program semantics.
- Test recommendations are based on changed file extensions and presence of test paths.
- The in-memory rate limiter is per process and is not a distributed quota.
- The parser is intentionally lightweight and is not a complete implementation of every Git diff extension. It decodes Git C-quoted UTF-8 paths and supports quoted file-header prefixes, including paths containing spaces.
- No GitHub App, persistent history, dashboard, LLM integration, or code execution is part of the current MVP.

## Extension guidance

Keep parsing, rule detection, scoring and recommendations independently testable. Give each rule a stable identifier and add both positive and negative examples. Add language-aware parsers only when their accuracy can be measured against a labeled corpus.
