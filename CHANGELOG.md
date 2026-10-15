# Changelog

Notable project changes are documented here. This project is an early MVP and does not yet follow a formal release cadence.

## Unreleased

### Added
- Responsive website workbench served by the FastAPI app and included in the Docker image.
- Explicit-origin CORS configuration for optional cross-origin deployments.
- Automatic pull-request diff triage workflow with read-only permissions.
- Parser regression tests for malformed and incomplete hunks and quoted Git paths.
- Repository banner, structured issue forms, pull-request checklist, editor defaults, and release-maintenance guidance.
- Render Blueprint and deployment documentation.

### Improved
- CI now checks Python lint, formatting, tests, compilation, and website JavaScript syntax.
- README navigation, feature/limitation table, quick-start instructions, API reference, and project layout.

### Known limitations
- No public demo has been deployed or smoke-tested yet.
- Risk rules are heuristics; representative precision and recall are not established.
- The API rate limiter is in-memory and per process.
- Full Git diff grammar coverage and fork/large-diff PR workflow scenarios still need validation.
