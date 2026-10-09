# Security Policy

## Scope

The current MVP accepts unified diffs and performs static string/path analysis. It does not clone repositories, execute code, install packages, or use an AI model.

## Reporting a vulnerability

Please do not publish secrets, tokens, or exploit details in a public issue. Contact the repository owner privately through GitHub to coordinate disclosure. Include the affected revision, impact, and a minimal reproduction where safe.

## Deployment guidance

- Do not expose an unauthenticated analysis endpoint to untrusted users without a gateway, rate limits and request-size controls.
- Treat submitted diffs and all repository text as untrusted data.
- Do not put credentials or private source in logs.
- Keep dependencies updated and run the CI checks before deployment.
- Do not add code execution to the API process. Any future test runner must be isolated, ephemeral, resource-limited, and denied ambient credentials and network access by default.
- The risk score is not a security guarantee.

This project is an early-stage MVP; a formal security audit has not been performed.
