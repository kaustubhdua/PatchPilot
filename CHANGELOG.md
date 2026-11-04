# Changelog

All notable changes to PatchPilot are documented here.

## Unreleased

### Added
- Include source file and new-line locations separately from evidence text for risky added-line findings.
- Expose malformed and incomplete diff hunk counts for each changed file.
- Include report-level analysis warnings when diff sections are malformed or incomplete.
- Display parser-integrity warnings in the web workbench, CLI, and GitHub Actions summary.
- Display risky finding source locations in CLI and GitHub Actions summaries.
- Avoid interpolating pull-request numbers and base SHAs directly into workflow shell commands.
- Add regression coverage for incomplete hunk reporting.

### Notes
- The warning is informational and does not reconstruct missing diff content.
- Results from malformed or incomplete hunks may contain partial statistics and findings.
