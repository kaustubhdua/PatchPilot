# Threat model

## Assets

- Private source code and diff contents
- GitHub credentials and installation tokens if integration is added
- Analysis integrity and availability
- Repository and installation metadata

## Threats and controls

| Threat | Current or required control |
|---|---|
| Oversized input / resource exhaustion | Request size bound; add deployment-level request/time limits |
| Repeated requests | Current per-process limiter; use shared gateway limits for multi-worker/public deployments |
| Sensitive code leaked in logs | Avoid logging request bodies and source snippets; review exception and proxy logging |
| Misleading results from malformed diffs | Conservative parser, regression fixtures, explicit limitations |
| False positives | Negative fixtures, evidence, severity explanation, suppressions with rationale |
| Forged GitHub webhook (future) | Verify HMAC signature and timestamp, reject invalid requests |
| Replayed webhook (future) | Persist delivery IDs and make handlers idempotent |
| Token leakage (future) | Minimum permissions, short-lived installation tokens, secret storage, rotation |
| Prompt injection (future LLM) | Treat source and comments as untrusted content; strict tool allowlists; no implicit execution |
| Untrusted code execution (future) | Do not execute in API process; isolated ephemeral runner, resource limits, no ambient secrets, network denied by default |

## Security posture

This is a threat-model starting point, not a formal security audit or certification. Reassess it whenever GitHub credentials, persistence, model providers, or code execution are introduced.
