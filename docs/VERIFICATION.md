# Verification evidence

Local checks performed on 2026-10-22 (Asia/Shanghai), Windows, Python 3.11.15.

| Check | Result |
| --- | --- |
| Ruff 0.17.1 | All checks passed |
| mypy 2.4.0 | No issues in 8 source files |
| unittest | 52 tests passed; includes nine release-audit regressions and parameterized cases |
| Demo scanner | Risky: 8 findings (5 high, 3 medium); hardened: 0 current-rule findings |
| Edge 155.0.4283.62 | Risky, hardened, diff and HTML-injection fixture all rendered; no page errors |
| Mobile 390px | No horizontal overflow |
| Report privacy | Synthetic raw credential values absent from text/JSON/HTML/SARIF and diff exports |
| Packaging | Wheel and sdist built; Twine accepted metadata of both |
| Clean wheel install | Fresh venv, no-index/no-deps, console entrypoint works outside source checkout; pip check passed |
| Release gate tests | Reject missing reviewers, empty reviewers, wildcard/tag/multiple branch policies; accept main-only reviewed environment |
| Runtime behavior | Tests prohibit subprocess creation and socket use during scan |
| Live release environment | GitHub API verified required reviewer and main-only policy; ACA_PUBLISH_ENABLED=false |
| GitHub CI | Ubuntu Python 3.11/3.13 and Windows Python 3.11 all passed for implementation revision f660528 |

Local evidence (ignored in git except for the small synthetic README preview):

- `research/research-pages.json`: four public primary-source pages read using Edge,
  all HTTP 200; third-party domains blocked.
- `research/verification.json`: browser version, context settings, finding counts,
  mobile overflow and JavaScript errors.
- `research/risky-desktop.png`, `research/risky-mobile.png`
- `research/hardened-desktop.png`, `research/diff-desktop.png`, `research/xss-desktop.png`
- `research/*-snapshot.txt`: semantic heading snapshots.
- `reports/`: generated HTML, text, JSON and SARIF for synthetic examples.
- `dist/`: wheel and sdist. Hashes recorded in the final delivery note.

Browser screenshots were visually inspected. HTML has no scripts or external
resources; XSS-like server names display as text. Disabled entries are deliberately
skipped by checks and still counted in the summary.

## Reproduce

```sh
python -m ruff check .
python -m mypy
python -m unittest discover -s tests -v
python -m build --no-isolation
python -m twine check dist/*
python -m tools.generate_demo
# Optional, with Edge installed:
npm install --prefix tools --ignore-scripts
node tools/browser-verify.cjs --research
node tools/browser-verify.cjs
```

Browser tooling resolves the optional Playwright module in tools/node_modules.
`ACA_PLAYWRIGHT_PATH` can select an existing installation; local verification used
Playwright 1.64.0 already present on this machine. QA uses `chromiumSandbox: true`,
fresh context, downloads disabled, no permissions and an explicit hostname
allowlist. It never opens personal browser profiles or logs into research sites.

Cross-platform GitHub CI passed for Ubuntu Python 3.11/3.13 and Windows Python
3.11: [PR run](https://github.com/miaomiao-lanmiao/agent-config-audit/actions/runs/39647530158).
Latest-revision checks remain visible on the PR. Main branch protection requires
all three matrix checks, including for administrators; force push and deletion
are disabled. GitHub environment protection has been verified through the API;
PyPI account-side trust still needs maintainer setup. No publication was run.

Public review: https://github.com/miaomiao-lanmiao/agent-config-audit/pull/1 .
