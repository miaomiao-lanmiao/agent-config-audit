# Agent Config Audit — delivery plan

## Positioning

A zero-runtime-dependency, offline preflight for MCP configuration reviews.
Inspect a configuration before starting its servers; compare revisions and export
redacted, reviewable findings. This is a heuristic review aid, not a sandbox,
malware detector, or certificate of safety.

## MVP (selected 2026-10-22, Asia/Shanghai)

1. Explicit-path JSON/JSONC inputs: `mcpServers`, `servers`, or `mcp.servers`.
2. Explain actionable configuration risks: plaintext credentials, mutable package
   versions, shell launchers, broad filesystem access, Docker privilege/mounts,
   insecure remote transport, and TLS bypass.
3. Compare two configurations: additions, removals, changed launch/transport/env
   fields and before/after findings; never export raw configuration values.
4. Deterministic text, JSON, SARIF 2.1.0 and standalone accessible HTML output,
   configurable CI failure threshold, and documented exit statuses.
5. Installable wheel/sdist, CI, verification evidence, and a disabled-by-default
   PyPI release workflow with an environment approval requirement.

## Structure

```
agent_config_audit/   parser, static rules, comparison, reports, CLI
examples/             synthetic risky / hardened configurations
tests/                unit and subprocess integration tests
tools/                browser verification and release preflight
research/             topic report, research metadata, ignored screenshots
docs/                 rules, release guide, PR draft, delivery evidence
.github/workflows/    lint + tests + build, manual gated release
```

## Dependencies and reasons

- Runtime: Python >=3.11 standard library only; no network or model keys.
- Build: setuptools + wheel, `build` frontend; standard wheel/sdist tooling.
- Development: Ruff (lint), mypy (static types), Twine (metadata check).
  Exact versions recorded in `requirements-dev.txt` after resolution.
- Browser QA only: Playwright 1.64.0, use existing local installation when
  available, otherwise `tools/package.json`. Edge stable with a fresh temporary
  context, downloads disabled, no permissions, default browser sandbox enabled.
- Network destinations used in research/QA: github.com, docs.github.com,
  pypi.org, docs.unity3d.com, modelcontextprotocol.io, code.visualstudio.com,
  packaging.python.org. Package fetches: pypi.org, files.pythonhosted.org.
  GitHub repository/API delivery uses github.com and api.github.com; interactive
  OAuth login is performed by the user in their browser, outside automated QA.
  All output files and temporary build/browser profiles stay in this workspace.

## Automated acceptance

- Ruff and mypy pass; unittest suite passes, covering malformed input, schema
  validation, rule positive/negative cases, placeholder secrets, redaction, XSS,
  disabled servers, CLI exit statuses, and deterministic exports.
- Static analysis never executes configuration commands or opens remote URLs.
- Demo findings are present for risky fixtures and absent for hardened fixtures.
- Diff flags an added server and changed configuration without raw values.
- HTML works offline on desktop/mobile in Edge with zero script errors; SARIF
  contains stable rule IDs and config JSON pointers.
- Wheel and sdist build, Twine check succeeds, wheel installs in a fresh venv
  without runtime dependencies and its console entrypoint works.
- Release preflight fails closed without required reviewers and PyPI setup;
  actual publish requires manual dispatch, reviewed main revision, environment
  approval, and PyPI trusted publishing (OIDC).

## Delivery / publication

PyPI is the primary distribution channel; GitHub is the source/showcase.
Use `feature/scaffold-agent-config-audit`, local conventional commits, and a PR.
No direct push to main, merge, force push, or real package publication.
For a new repository, initialize a small README-only main through the GitHub
repository creation API, then push the feature branch and open a PR.
GitHub login is handled interactively by the user. Package-name availability is
not ownership; verify the PyPI project/pending publisher before any release.

## Environment constraints

The host session has unrestricted filesystem permissions; this task cannot
change the host sandbox policy. We enforce the narrower working scope in our
actions: write only under this project, no personal config/credentials access,
no sandbox-disabling browser flags, and explicit research network allowlists.
No claim of OS-level network isolation is made.
