# Roadmap

PatchPilot is being built in incremental, testable milestones. Items below are goals, not claims that the functionality exists.

## M0 — Reliable foundation
- [x] FastAPI API and Pydantic input limits
- [x] Deterministic baseline rules and evidence
- [x] Unit/API tests and CI workflow
- [x] Non-root container and health check
- [ ] Confirm green CI and add parser fixture corpus
- [ ] Fully support quoted paths, renames, deleted files, and malformed diffs

## M1 — Better diff intelligence
- [ ] Separate parser, rule engine, scoring and recommendation modules
- [ ] Add language-aware rules and syntax-aware parsing
- [ ] Add rule configuration and severity/score explanations
- [ ] Build positive and negative fixtures for each rule
- [ ] Measure precision, recall and false-positive rate

## M2 — GitHub integration
- [ ] GitHub App with minimum permissions and short-lived installation tokens
- [ ] Verify webhook signatures and make delivery handling idempotent
- [ ] Fetch pull-request metadata and changed-file patches safely
- [ ] Publish an opt-in Check Run with inline evidence
- [ ] Handle pagination, rate limits, retries and oversized diffs

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
- [ ] Benchmark dataset, baselines and reproducible evaluation
- [ ] Threat model, dependency scanning, observability and incident runbooks
- [ ] Staging deployment, backup/restore test and documented limitations
- [ ] Public demo and short end-to-end walkthrough

## Release gate

A credible first public release should analyze a real authorized pull request, provide reproducible evidence for each finding, suggest relevant tests, pass CI, document known limitations, and never execute submitted code in the API process.
