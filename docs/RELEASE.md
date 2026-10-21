# Release guide — explicit human approval

## Current state

0.1.0 is a local release candidate. No PyPI upload has been performed.
`ci.yml` runs lint, types, tests, builds and metadata checks; its `release-gate`
job references the `release-review` environment and never publishes. Environment
names in YAML alone do not configure required reviewers.

## Repository setup

1. Review and manually merge the feature PR. Do not push this implementation
   directly to main.
2. Enable private vulnerability reporting. Configure branch protection and
   required CI checks for main.
3. Configure `release-review` and `pypi-release` with required reviewers. On
   `pypi-release`, use selected deployment branches: **main only**, no tags.
   Decide whether initiators may approve their own release; personal repositories
   may have only one maintainer.
4. Run `python tools/release_preflight.py --repo OWNER/REPO`; a missing environment,
   missing reviewers, ambiguous policy, authorization failure, wildcard branch or
   missing main-only restriction blocks publication.

## PyPI setup

1. Verify the project name is available/owned by you. A 404 from a name lookup is
   not a reservation.
2. Configure a PyPI pending/trusted publisher for your GitHub owner/repository,
   workflow `release.yml`, environment `pypi-release`. Use OIDC, no long-lived PAT
   or PyPI token. The offline preflight cannot verify PyPI account ownership.
3. Inspect the wheel/sdist and their metadata. Install the wheel in a fresh
   environment and run its CLI outside the source directory.
4. Set repository Actions variable `ACA_PUBLISH_ENABLED=true` only after the
   above setup and review. Missing/false keeps the workflow inert.

## What approval does

Manually dispatch **Publish to PyPI (manual approval)** on main with `publish=true`.
The prepare job verifies protection, repeats checks and packages artifacts.
The publish job then waits for `pypi-release` required reviewer approval.
Approving that job lets GitHub obtain a short-lived OIDC identity and upload
the wheel/sdist to PyPI using trusted publishing. It does not merge a PR or
deploy a website. Do not dispatch this workflow without user approval.

## Rollback / recovery

Before release: revert local commits or close the PR; no production changed.
After a publication: PyPI versions cannot be overwritten. Investigate, yank a
bad release if needed and publish a fixed version through the same manual gate.
Do not delete the repository, rewrite public history or reuse an uploaded version.

Sources: [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments),
[PyPA trusted-publishing workflow](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
