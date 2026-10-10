# Benchmark methodology

PatchPilot must not claim detection quality without a reproducible labeled dataset.

## Dataset format

Store one case per JSON object with:
- `id`: stable case identifier
- `diff`: unified diff text
- `expected_rule_ids`: rule IDs expected for the case
- `notes`: why the case is included

Include positive cases, benign negative cases, malformed diffs, multiple files, binary files, renames, dependency changes, and false-positive traps such as risky tokens inside comments or test fixtures.

## Metrics

For each rule, report:
- True positives (TP)
- False positives (FP)
- False negatives (FN)
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)

If a denominator is zero, report the metric as unavailable rather than inventing a value. Also record elapsed time and dataset version. Do not present a tiny hand-authored corpus as evidence of production accuracy.

## Reproducibility

- Version the dataset and scoring script.
- Document how expected labels were assigned.
- Run the same benchmark before and after rule changes.
- Keep difficult negative cases permanently as regression tests.
- Publish limitations and dataset size alongside results.

The repository does not yet claim measured precision or recall. This document defines the process needed before publishing those claims.
