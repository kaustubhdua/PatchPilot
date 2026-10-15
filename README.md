# PatchPilot

<p align="center">
  <strong>Explainable pull-request risk triage — without executing submitted code.</strong>
</p>

<p align="center">
  <a href="https://github.com/kaustubhdua/PatchPilot/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/kaustubhdua/PatchPilot/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/kaustubhdua/PatchPilot/actions/workflows/security.yml"><img alt="Security checks" src="https://github.com/kaustubhdua/PatchPilot/actions/workflows/security.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/kaustubhdua/PatchPilot/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-3776AB.svg">
  <img alt="Status: early MVP" src="https://img.shields.io/badge/status-early%20MVP-orange.svg">
</p>

PatchPilot inspects a unified diff and returns changed-file statistics, evidence-backed static signals, a coarse risk score, and test suggestions. It is designed to make code review more structured and explainable. The MVP parses diffs as untrusted text: it does **not** clone repositories, execute patches, install submitted dependencies, or call an LLM.

> **Status:** early MVP. The automated pull-request workflow and core analysis are implemented, but this project is not a hosted service, a formal security audit, or an autonomous code-fixing agent. See the [roadmap](ROADMAP.md) and current [CI status](https://github.com/kaustubhdua/PatchPilot/actions).

## At a glance

- **Explainable:** findings include stable rule IDs, descriptions, and evidence.
- **Conservative boundary:** analyzes diff text only; no execution of pull-request code.
- **Usable locally:** Python API, CLI, and Docker image.
- **GitHub workflow:** a pull-request workflow can publish a concise analysis summary.
- **Honest evaluation:** a starter benchmark is included, with explicit warnings that it is not representative production evidence.

## Contents

- [Website](#website)
- [Quick start](#quick-start)
- [CLI](#command-line)
- [API](#api)
- [Rules and limitations](#rules-and-limitations)
- [GitHub Actions integration](#github-actions-integration)
- [Benchmark](#benchmark)
- [Security](#security-boundary)
- [Development](#development)

## Website

A responsive static web client lives in [`website/`](website/). The GitHub Pages workflow deploys it from the repository root of that directory. The browser client sends diffs only to the API endpoint configured in the workbench; no API URL is hard-coded as a hosted service.

To preview it locally, serve the folder with any static HTTP server, for example `python -m http.server 8080 --directory website`, then open `http://127.0.0.1:8080`. Start the API separately. For cross-origin use, configure `PATCHPILOT_CORS_ORIGINS` on the API to a comma-separated list of exact trusted origins (for example, your deployed Pages origin). CORS is disabled by default; do not use wildcard origins for a public API.

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

## Command line

Analyze a saved patch:

```bash
patchpilot analyze --diff-file change.diff
```

Analyze the current branch against the main branch:

```bash
git diff origin/main...HEAD | patchpilot analyze --title "Review current branch"
```

Get machine-readable output:

```bash
git diff origin/main...HEAD | patchpilot analyze --json
```

The CLI reads a patch from a file or standard input, prints findings and suggested checks, and exits non-zero for invalid input.

## API

- `GET /health` — liveness probe.
- `GET /ready` — readiness probe for the stateless MVP.
- `POST /v1/analyze` — validate and analyze a unified diff.

Example request:

```json
{
  "title": "Harden request validation",
  "base_ref": "main",
  "head_ref": "feature/validation",
  "diff": "diff --git a/src/example.py b/src/example.py\\n--- a/src/example.py\\n+++ b/src/example.py\\n@@ -1 +1 @@\\n-old()\\n+new()"
}
```

Input is limited to 500,000 characters and unknown request fields are rejected. Analysis is rate-limited to 60 requests per client IP per 60-second window **per process**; this is a basic safety rail, not a shared limiter for multi-worker/public deployments. Responses include a heuristic score from 0–100, broad risk level, file statistics, findings, and suggested tests.

## Rules and limitations

The current rules look for:
- Paths whose names suggest authentication or security sensitivity
- Dependency manifest and lockfile changes
- Broad changes and large diffs
- Risky patterns in added lines (for example dynamic evaluation, shell execution, or disabled TLS verification)
- Production changes without a corresponding test file in the same diff

These are heuristics, not semantic analysis. Path-name matching can be noisy; a risky-looking token may be benign, and no findings do not prove a change is safe. The score is **not** a probability of defects, security certification, or merge recommendation. Binary files are counted but their contents are not analyzed. Full Git diff grammar coverage and a broad, real-world fixture corpus remain outstanding.

## GitHub Actions integration

The pull-request workflow analyzes the diff using the trusted base revision and publishes a summary. It is designed not to check out or execute pull-request head code. It uses read-only repository and pull-request permissions. The workflow is a triage aid only and should not be used as a merge gate without independent validation.

- [Pull-request analysis workflow](.github/workflows/patchpilot-pr.yml)
- [CI workflow](.github/workflows/ci.yml)
- [Security checks](.github/workflows/security.yml)

## Benchmark

Run the starter corpus:

```bash
python scripts/benchmark.py
```

The corpus and script make current behavior reproducible; they do **not** demonstrate production precision or recall. Expand and independently label representative examples, including false positives, before making quality claims. See [benchmark methodology](docs/benchmark-methodology.md).

## Security boundary

PatchPilot treats the supplied diff as untrusted text. It does not clone repositories, run tests, install dependencies, execute patches, or call an LLM. Do not send secrets or private code to a deployment unless its data-handling policy is appropriate for that repository.

See [SECURITY.md](SECURITY.md) for deployment guidance and vulnerability reporting. A formal security audit has not been performed.

## Architecture and roadmap

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat-model.md)
- [Roadmap](ROADMAP.md)

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest
python scripts/benchmark.py
```

Contributions should include regression tests and preserve deterministic, evidence-backed findings. See [CONTRIBUTING.md](CONTRIBUTING.md).
