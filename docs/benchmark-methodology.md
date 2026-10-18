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


## Reviewer-labelled triage corpus v1

`benchmarks/triage-labeled-v1.jsonl` adds 20 small synthetic cases with reviewer-authored expected rule IDs and test-suggestion labels. It includes risky constructs, comment-only false-positive traps, test-file examples, dependency manifests, sensitive paths, binary assets, documentation-only changes, multi-file thresholds, and a large synthetic diff.

Run:

```bash
python scripts/benchmark_labeled.py
```

The script reports TP, FP, FN, precision, recall, F1 and exact-set agreement for configured rule findings and proposed test categories. Test-suggestion precision is shown as relevance: the share of produced suggestions that reviewers labelled useful for that case.

Labels follow a **triage relevance policy**, not a vulnerability oracle. A `sensitive-path` true positive means the path deserves review, not that it contains a vulnerability. A false positive or false negative is relative to these explicit fixture labels only.

The v1 corpus is synthetic, small, hand-labelled and authored alongside the heuristics. It has not been independently adjudicated and is not representative of the distribution of real pull requests. Do not present its scores as production accuracy. The original 12-case `cases.jsonl` remains a behavior/regression corpus and should not be combined with this labelled set without reconciling the label policy.
