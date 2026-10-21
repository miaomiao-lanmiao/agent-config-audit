## Summary

- Add a zero-runtime-dependency offline preflight for MCP JSON/JSONC configs.
- Implement twelve documented heuristic rules, field-level configuration drift,
  deterministic text/JSON/HTML/SARIF output and CI failure thresholds.
- Omit raw command, argument, env, header and URL values from all reports/errors.
- Include synthetic demos, English contributor documentation, Chinese topic
  research, an MIT license and a compact README preview.
- Add Linux/Windows verification CI and disabled-by-default manual PyPI release
  with environment checks, required approval and OIDC publishing.

## Local quick start (repository root, PowerShell)

```powershell
python -m pip install --no-deps .
agent-config-audit scan examples/risky.json --format html -o reports/review.html --fail-on none
Start-Process reports/review.html
```

## Verification

- Ruff: all checks passed. mypy: no issues in 8 source files.
- unittest: 43 tests passed (additional parameterized edge cases included).
- Wheel and sdist built; Twine metadata checks passed.
- Wheel installed offline into a fresh venv with no dependencies; entrypoint
  works outside the source directory and pip check passes.
- Edge 155.0.4283.62: risky (8 findings), hardened (0), diff (0 after findings)
  and escaped HTML-injection fixture render without page errors.
- Mobile viewport 390px: no horizontal overflow.
- Fresh browser context, default Chromium sandbox enabled, downloads disabled,
  permissions empty, external requests blocked outside explicit research allowlist.

## Screenshots

- Committed compact synthetic preview: `research/preview.png` (about 89 KiB).
- Local full screenshots: `research/risky-desktop.png`,
  `research/risky-mobile.png`, `research/hardened-desktop.png`,
  `research/diff-desktop.png`, `research/xss-desktop.png`.
- Reproduction and scope: `docs/VERIFICATION.md`.

## Known limits

- Heuristics do not inspect package/script contents, tool catalogs or live
  permissions; no findings does not establish safety.
- JSON/JSONC only; explicit paths only; no TOML or automatic discovery.
- Report server names/JSON pointers are intentionally included and must not
  contain secrets. SARIF uses logical locations, not source line annotations.
- Example package versions illustrate exact pinning; existence is not checked.
- Local checks were performed on Windows Python 3.11; remote CI results should
  be reviewed separately. No package has been published.

## Before publication

- [ ] Review and manually merge this PR.
- [ ] Verify required reviewers and main-only deployment policy.
- [ ] Configure PyPI pending/trusted publisher for this repository, release.yml
      and pypi-release; confirm project name ownership/availability.
- [ ] Inspect artifacts, then set ACA_PUBLISH_ENABLED=true.
- [ ] Explicitly authorize and manually dispatch publication with publish=true.
- [ ] Approve the pypi-release job; it uploads wheel/sdist through OIDC.

## Rollback

Close the PR before merge, or revert its commits after merge. No production
service has changed. PyPI versions cannot be overwritten after publication.
