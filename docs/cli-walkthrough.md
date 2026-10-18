# PatchPilot CLI walkthrough

This walkthrough is intentionally local and offline. It uses a small, synthetic unified diff and does not connect to GitHub, clone a repository, execute submitted code, or call a model.

## 1. Install the development environment

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
~~~

## 2. Run the included example

~~~bash
patchpilot analyze --diff-file examples/tls-verification-change.diff --title "Review TLS configuration"
~~~

The current rules should flag the new `verify=False` line as `tls-verification-disabled`. Because the path is security-sensitive and production code changed without a test path in the diff, the output can include additional path/test-coverage signals. The exact numeric risk score is a heuristic output; treat the findings as triage prompts, not a security conclusion.

For machine-readable output:

~~~bash
patchpilot analyze --diff-file examples/tls-verification-change.diff --json
~~~

## 3. Run the regression checks

~~~bash
ruff check .
ruff format --check .
pytest
python scripts/benchmark.py
~~~

The benchmark uses the small, hand-authored synthetic corpus under `benchmarks/cases.jsonl`. It is a rule-regression tool, not representative detection-quality evidence. Do not quote its precision or recall as real-world quality.

## 4. Review before using on real changes

- Inspect the generated evidence lines and open the changed source yourself.
- Check whether each heuristic signal is relevant to this patch.
- Inspect the test suggestions and run the project’s actual tests separately.
- Do not use a low score or an empty finding list as proof of safety.

This walkthrough is reproducible for a local checkout. It is not a hosted public demo, a formal security audit, or a merge recommendation.
