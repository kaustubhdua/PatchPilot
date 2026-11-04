# Changelog

All notable changes to PatchPilot are documented here.

## Unreleased

### Added
- Include source file and new-line locations separately from evidence text for risky added-line findings.
- Expose malformed and incomplete diff hunk counts for each changed file.
- Include report-level analysis warnings when diff sections are malformed or incomplete.
- Display parser-integrity warnings in the web workbench summary.
- Add regression coverage for incomplete hunk reporting.

### Notes
- The warning is informational and does not reconstruct missing diff content.
- Results from malformed or incomplete hunks may contain partial statistics and findings.
