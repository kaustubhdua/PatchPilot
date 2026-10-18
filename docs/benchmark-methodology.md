# Benchmark methodology

PatchPilot must not claim detection quality without a reproducible labeled dataset.

## Dataset format

Store one case per JSON object with:
- `id`: stable case identifier
- `diff`: unified diff text
- `expected_rule_ids`: rule IDs expected for the case
- `notes`: why the case is included

Include positive cases, benign negative cases, malformed diffs, multiple files, binary files, renames, dependency changes, and false-positive traps such as risky tokens inside comments or test fixtures. The current 12-case corpus includes a few deliberate negative traps. It is a regression suite, not an independent representative sample: some labels intentionally capture the current heuristic output rather than semantic security truth.

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

The repository does not yet claim measured precision or recall. The current 12-case corpus contains deliberately curated synthetic diffs, including known false-positive traps; any score printed from it is a rule-regression count only. Do not publish it as a real-world precision/recall estimate. Broader real Git-generated diffs and independently reviewed labels are still required.
