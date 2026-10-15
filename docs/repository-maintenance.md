# Repository maintenance

## Before merging

1. Keep changes focused and explain the motivation in the pull request.
2. Add a regression test for every fixed defect or behavior change.
3. Run CI locally where practical: Ruff lint/format, pytest, Python compilation, and website JavaScript syntax validation.
4. Review dependency audit results and investigate new vulnerabilities.
5. Never execute pull-request code in the privileged API or analysis workflow.
6. Update the README, architecture, security docs, or roadmap when supported behavior changes.

## Release checklist

- [ ] CI and security checks pass on the release commit.
- [ ] Run the benchmark and review its output; do not claim production precision/recall from the starter corpus.
- [ ] Check the Docker image starts and API health/readiness probes respond.
- [ ] Smoke-test the web workbench against the deployed API with a non-sensitive fixture.
- [ ] Confirm the deployment uses exact CORS origins if cross-origin hosting is enabled.
- [ ] Review logs and rate limiting for the chosen deployment topology.
- [ ] Document known issues, compatibility changes, and release notes.
- [ ] Create a version tag only after release validation.

## Repository settings recommended for maintainers

- Protect main with required CI checks and block force pushes.
- Require pull requests and at least one review when collaborators are available.
- Enable deletion of head branches after merge.
- Enable Dependabot alerts and security updates.
- Use least-privilege workflow permissions and pin third-party actions to reviewed versions or immutable SHAs according to the team's supply-chain policy.
- Keep a release checklist and avoid publishing a hosted demo until deployment has been smoke-tested.

Some settings require repository-admin UI or API permissions and are not changed by committing files.
