# Release audit — 0.1.0

Date: 2026-10-22 (Asia/Shanghai). Scope: the Python scanner, JSONC parser,
report escaping/redaction, file output, static rules, packaging, CI and release
permissions. The user explicitly requested self-audit followed by publication.

## Findings and repairs

1. Invalid JSON handling: NaN/Infinity were accepted; oversized integer literals
   raised an uncaught ValueError; a comma in an otherwise empty object/array was
   incorrectly removed. Reject non-finite values, preserve invalid commas, and
   convert integer conversion failures to sanitized ConfigError messages.
2. Windows launcher variants: .exe/.cmd forms did not consistently receive the
   package-launch checks. Normalize executable suffixes before rule selection.
3. npm local scripts: `npm run server` was incorrectly treated as an unpinned
   package installation. Limit npm launch checks to `exec`/`x`.
4. Filesystem arguments: assignment syntax such as `--directory=/` skipped the
   broad-scope check. Inspect assignment values as well as positional arguments.
5. URLs: percent-encoded credential parameter names and control characters were
   missed. Decode query keys once and flag controls before URL normalization.
6. Release metadata: malformed deployment policy types caused an unhandled
   exception. Treat invalid metadata as a failed preflight check.

Nine regression tests reproduce these issues (including parameterized variants).
They failed before the fixes; the release candidate must pass all 52 tests plus
lint, type checking, browser QA, packaging and Linux/Windows CI before merge.

## Scope checks

- Runtime has no third-party dependencies or telemetry, subprocess or network
  calls. Existing behavioral tests prohibit process/socket use during scanning.
- HTML labels and pointers are escaped; CSP blocks scripts and external content.
- No raw env/header/argument/URL values are serialized into reports or errors.
- Exclusive output creation prevents overwriting an existing file/input.
- GitHub Actions dependencies are pinned to verified upstream commit hashes.
- Publication uses OIDC, a protected environment, main-only policy and a manual
  workflow. Repository protection is retained for this authorized release.

This is a bounded first-party review, not an independent penetration test or a
guarantee that all configuration risks are detected. PyPI account-side publisher
registration must match the GitHub workflow before an OIDC upload can succeed.
