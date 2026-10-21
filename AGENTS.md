# Contributor agent instructions

- Keep all project writes under this repository. Never inspect real secrets or
  personal MCP configurations for testing. Use synthetic fixtures.
- Runtime must remain Python >=3.11 standard library only. Update PLAN.md before
  adding dependencies; explain the reason.
- Scanning must never execute a configured command or contact a configured URL.
- Reports and errors must omit raw config values. Names, JSON pointers and digest
  metadata are the only configuration identifiers intended for output.
- No automatic home-directory discovery, environment interpolation, remediation
  or file overwrites. Avoid treating heuristic findings as proof of compromise.
- Before committing: Ruff, mypy, unittest, wheel/sdist build, Twine metadata check.
  Re-run the relevant checks after code changes.
- Use a feature branch and conventional commits. No direct main push, automatic
  merge, force push or repository deletion.
- Actual PyPI publication needs explicit human approval and a protected release
  environment. Never dispatch a publishing run without user approval.
- Edge QA: channel msedge, headless, chromiumSandbox true, fresh context,
  downloads false, permissions empty, request allowlist. Store screenshots in
  research/ and do not commit large screenshots or personal browser content.
