# Roadmap

PatchPilot is built in incremental, testable milestones. A checked item means the capability or artifact exists in the repository; it does not imply that the latest CI run is green or that production readiness has been independently verified.

## M0 — Reliable foundation
- [x] FastAPI API and Pydantic input limits
- [x] Deterministic baseline rules and evidence
- [x] Unit/API tests and CI workflow
- [x] Non-root container and health check
- [x] Architecture, threat-model and benchmark-methodology documents
- [x] Starter benchmark corpus and metric script
- [x] Additional parser regression tests
- [x] Manual GitHub Actions diff-analysis workflow
- [x] Scheduled dependency audit and basic secret-pattern check
- [ ] Run CI and verify latest result
- [ ] Expand real Git-generated diff fixture corpus
- [ ] Validate full hunk counts, truncation and all relevant Git path encodings
- [ ] Review dependency-audit and secret-check workflows for false positives and operational fit

## M1 — Better diff intelligence
- [ ] Separate parser, rule interface, scoring and recommendation modules where useful
- [ ] Add language-aware and syntax-aware analysis
- [ ] Add rule configuration, stable metadata and severity/score explanations
- [ ] Add positive and negative fixtures for every rule
- [ ] Measure precision, recall, false-positive rate and latency on a labeled dataset
- [ ] Add suppressions with documented rationale and duplicate finding handling

## M2 — GitHub integration
- [x] Manual GitHub Actions workflow to analyze a selected diff and upload a report artifact
- [ ] Automatically run on pull requests and publish a concise summary
- [ ] Map findings to changed lines when supported by reliable evidence
- [ ] Handle forks, permissions, oversized diffs and no-diff cases safely
- [ ] GitHub App with minimum permissions and short-lived installation tokens, if needed
- [ ] Verify webhook signatures and make delivery handling idempotent if webhooks are used
- [ ] Handle pagination, rate limits, retries and unavailable patches

## M3 — Codebase context
- [ ] Symbol index and dependency/call graph
- [ ] Change-impact analysis and relevant test discovery
- [ ] Versioned snapshots with retention and deletion controls

## M4 — Product experience
- [ ] Dashboard for repositories, pull requests and past analyses
- [ ] Evidence viewer with changed-line context
- [ ] Background jobs, progress states and retry visibility
- [ ] Authentication, authorization and audit events

## M5 — Assisted debugging
- [ ] Pluggable model-provider interface
- [ ] Retrieval-grounded diagnosis with file/line evidence
- [ ] Proposed patches and regression tests, always marked as suggestions
- [ ] Prompt-injection defenses and strict tool allowlists
- [ ] No automatic commit or merge without explicit approval

## M6 — Safe validation and release
- [ ] Disposable, isolated runners with CPU, memory, time and disk limits
- [ ] No ambient secrets; deny network access by default
- [ ] Representative benchmark dataset, baselines and reproducible evaluation
- [ ] Threat model, dependency scanning, observability and incident runbooks
- [ ] Staging deployment, backup/restore test if persistence is added, and documented limitations
- [ ] Public demo and short end-to-end walkthrough

## Release gate

A credible first public release should analyze a real authorized pull request, provide reproducible evidence for each finding, suggest relevant tests, pass CI, document known limitations, and never execute submitted code in the API process.
