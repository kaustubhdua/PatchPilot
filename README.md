# PatchPilot

**Explainable pull-request risk triage, starting with deterministic diff analysis.**

PatchPilot inspects a unified diff and returns changed-file statistics, evidence-backed static signals, a coarse risk score, and test suggestions. The current MVP is intentionally small: it parses diffs only and never clones or executes repository code.

[Quick start](#quick-start) · [API](#api) · [Rules and limitations](#rules-and-limitations) · [Roadmap](ROADMAP.md) · [Security](SECURITY.md)

## Current status

- [x] FastAPI service with health and analysis endpoints
- [x] Request validation and bounded diff input
- [x] Deterministic risk heuristics with evidence
- [x] Unit and API regression tests
- [x] CI for lint, formatting and tests
- [x] Non-root Docker image and health check
- [ ] GitHub App / pull-request integration
- [ ] Syntax-aware parsing and language-specific rules
- [ ] Persistent history, dashboard and background jobs
- [ ] Benchmark and measured false-positive rates

This is an early MVP, not yet a hosted service or an autonomous code-fixing agent.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest
uvicorn patchpilot.api:app --reload
```

Open the interactive API docs at http://127.0.0.1:8000/docs.

## Command-line usage

Analyze a saved patch locally without starting the API:

```bash
patchpilot analyze --diff-file change.diff
git diff origin/main...HEAD | patchpilot analyze --title "Review current branch"
git diff origin/main...HEAD | patchpilot analyze --json
```

The CLI reads a patch from a file or standard input, prints evidence-backed findings, and exits with a non-zero status for invalid input. It does not clone a repository or execute patch contents.

## API

`GET /health` returns service health.

`POST /v1/analyze` accepts JSON:

```json
{
  "title": "Harden request validation",
  "base_ref": "main",
  "head_ref": "feature/validation",
  "diff": "diff --git a/src/example.py b/src/example.py\n--- a/src/example.py\n+++ b/src/example.py\n@@ -1 +1 @@\n-old()\n+new()"
}
```

The diff must be between 1 and 500,000 characters. Unknown request fields are rejected. The response contains a score from 0–100, a broad risk level, per-file line counts, findings with rule IDs and evidence, and suggested tests.

## Rules and limitations

The first version looks for:
- Changes to paths whose names suggest authentication or security sensitivity
- Dependency manifest and lockfile changes
- Broad changes and large diffs
- Risky patterns in **added lines** (for example, dynamic evaluation, shell execution, or disabled TLS verification)
- Production changes without a corresponding test file in the same diff

These are explainable heuristics, not semantic analysis. Path-name matching can be noisy; a risky-looking token may be benign, and the absence of findings is not evidence that a change is safe. The score is **not** a probability of defects, security certification, or merge recommendation. Binary files are counted but their contents are not analyzed. Unified-diff path quoting and every Git rename edge case are not yet fully supported.

## Security boundary

PatchPilot currently treats the supplied diff as untrusted text. It does not clone repositories, run tests, install dependencies, execute patches, or call an LLM. Do not send secrets or private code to a deployment unless its data-handling policy is appropriate for that repository.

See [SECURITY.md](SECURITY.md) before exposing an instance publicly.

## Development

- Keep rules deterministic and include the evidence that caused each finding.
- Add regression fixtures for parser edge cases and false positives.
- Never execute user-controlled repository code in the API process.
- Run the same lint, format and test checks as CI before submitting a change.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).
