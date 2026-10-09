# Contributing

Thanks for helping improve PatchPilot. The project prioritizes explainable results, conservative security boundaries, and regression-tested behavior.

## Before opening a pull request

1. Create or update tests for behavior changes, including false-positive cases.
2. Run:
   ```bash
   ruff check .
   ruff format --check .
   pytest
   ```
3. Keep findings evidence-backed and deterministic.
4. Update documentation when rules, limitations or API contracts change.

## Design principles

- Parse submitted diffs as data; never execute them.
- Avoid claims that a heuristic score predicts defect probability.
- Bound untrusted inputs and fail clearly on invalid requests.
- Prefer small, reviewable changes over speculative framework additions.
- Do not commit secrets, real credentials, or private repository contents.

## Pull request checklist

- [ ] Tests cover expected behavior and relevant edge cases
- [ ] Lint and formatting checks pass
- [ ] API or rule behavior is documented
- [ ] No repository code is executed
- [ ] Limitations and security implications are described
