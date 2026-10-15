# Deployment

PatchPilot's Docker image serves both the FastAPI endpoints and the responsive website from the same origin. This avoids requiring browser CORS configuration for the standard single-service deployment.

## Render Blueprint

1. Sign in to Render and choose **New → Blueprint**.
2. Connect the `kaustubhdua/PatchPilot` GitHub repository and select the branch containing `render.yaml`.
3. Review the Docker web service before creating it. The starter configuration uses Render's free plan, which may sleep when idle and is not a production SLA.
4. Wait for the first deployment to become healthy. Check `/health`, `/ready`, `/`, and `/docs` on the service URL.
5. If using a separate website origin, set `PATCHPILOT_CORS_ORIGINS` to a comma-separated list of exact trusted origins. Leave it unset for same-origin use. Never use `*` for a public API.

## Before public production use

- Put the service behind an appropriate gateway/WAF and shared rate limiter; the current limiter is in-memory and per process.
- Define access controls and data-retention/logging policies before accepting private source code.
- Monitor request volume, error rates and resource use; configure alerts and incident response.
- Pin and regularly update dependencies and container base images; review audit findings before deployment.
- Do not expose secrets in logs. Do not add execution of pull-request code to the API container.
- Run the CI and security workflows on the release commit.

The app currently does not require a database or persistent disk. The risk score is a heuristic triage signal, not a security guarantee or merge decision.
