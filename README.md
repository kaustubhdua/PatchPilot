# PatchPilot

Explainable pull-request risk analysis from unified diffs. The MVP uses deterministic, evidence-backed heuristics and never executes repository code.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
uvicorn patchpilot.api:app --reload
```

Open http://127.0.0.1:8000/docs.

## API

`POST /v1/analyze` accepts `title`, `base_ref`, `head_ref`, and a unified `diff`. It returns changed files, a 0–100 heuristic score, findings with evidence, and suggested tests. This score is triage—not a probability of defects, security audit, or merge recommendation.

## Security boundary

This MVP parses diffs only. It does not clone or run submitted code. Before adding execution, use disposable sandboxes, strict resource limits, no ambient credentials and restricted networking.
