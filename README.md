# Agent Config Audit

**Know what you're about to run.**

An offline preflight for MCP server configurations. Inspect risks, review
configuration drift, and share reports without copying launch arguments or
credential values into them.

**Python 3.11+ · zero runtime dependencies · MIT · no server execution · no telemetry**

![Offline MCP configuration report with prioritized findings](https://raw.githubusercontent.com/miaomiao-lanmiao/agent-config-audit/feature/scaffold-agent-config-audit/research/preview.png)

## Try it locally

From the repository root:

```powershell
python -m pip install --no-deps .
agent-config-audit scan examples/risky.json --format html --output reports/review.html --fail-on none
Start-Process reports/review.html
```

On macOS/Linux, open the generated HTML with your usual browser. Without
installing, use `python -m agent_config_audit` in place of `agent-config-audit`.
The examples are synthetic. Example version numbers illustrate pinning; package
existence and behavior are not verified by this tool. Environment reference
syntax must be supported by your MCP client.

## What you can do

```sh
# CI gate: high-severity findings return exit status 1.
agent-config-audit scan path/to/mcp.json

# Review JSONC from VS Code; export structured findings.
agent-config-audit scan examples/vscode.jsonc --format json

# Compare revisions; field names are shown, values are omitted.
agent-config-audit diff examples/risky.json examples/hardened.json

# Fail when any configuration changes, even if it introduces no known risk.
agent-config-audit diff before.json after.json --fail-on-change

# Export SARIF 2.1.0 for downstream tooling.
agent-config-audit scan examples/risky.json --format sarif -o reports/audit.sarif --fail-on none
```

Output files are created exclusively. Existing files, including input files, are
never overwritten. Choose a new path for each run. Reports are deterministic for
the same input bytes and tool version.

| Exit | Meaning |
| --- | --- |
| `0` | No findings at or above your chosen threshold; no gated drift |
| `1` | Findings meet the threshold, or `--fail-on-change` found drift |
| `2` | Invalid arguments/input, unreadable input, or output creation failed |

`--fail-on high|medium|low|none` defaults to `high`, configurable with
`ACA_FAIL_ON`. `none` still emits findings. An operational error still returns 2.
Diff thresholds apply to the **after** configuration; drift can be gated
separately. JSON includes before findings; SARIF includes after findings and
field-level change metadata. HTML/text show after findings and change categories.

## Input formats

JSON or JSONC with exactly one server collection:

```json
{"mcpServers": {"service": {"url": "https://mcp.example.com/mcp"}}}
```

Also accepts top-level `servers` or nested `mcp.servers`. Handles UTF-8 BOM,
comments and trailing commas without damaging URLs/quoted text. Duplicate keys,
ambiguous collections, invalid field types and inputs over 2 MiB are rejected.
Disabled entries (`disabled: true`) are counted but skipped by risk checks.
Only explicit paths are read. There is no home-directory discovery or recursive
scan. TOML and tool descriptor analysis are outside this version's scope.

## Checks

Twelve documented rules cover inline credentials, mutable npx/uvx versions,
shell launchers, broad filesystem arguments, privileged containers, sensitive
mounts, insecure HTTP, TLS bypass, automatic package confirmation and
credential-bearing or malformed URLs. See [the rule reference](docs/RULES.md).

Findings are review prompts. A shell launcher or filesystem root is sometimes
intentional. A pinned package can still be malicious. Indirect launches, script
contents, container image contents, tool poisoning and runtime permissions are
not analyzed. **No findings does not establish safety.**

## Privacy and report handling

The scanner uses no network and never starts configured commands. Raw command,
argument, environment, header and URL values are omitted from reports, including
diffs and parse errors. Server **names**, JSON pointers and an input SHA-256 digest
are included. Do not put secrets into server names; review reports before sharing.
This is configuration review, not a general-purpose secret scanner.

HTML is standalone with no scripts, remote fonts, images or analytics. A content
security policy blocks active content. Text output removes terminal control
characters from server names. SARIF uses logical JSON-pointer locations; some
platforms may require physical file locations for inline code annotations.

## Development

```sh
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m mypy
python -m unittest discover -s tests -v
python -m build --no-isolation
python -m twine check dist/*
```

Optional Edge QA is documented in [verification](docs/VERIFICATION.md).
See [CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md), and
[the release guide](docs/RELEASE.md).

## Release status

Version 0.1.0 is a release candidate, **not published to PyPI**. Install from a
local checkout or built wheel. CI packages artifacts; real publication is
disabled by default and requires manual dispatch, a reviewed `main` revision,
configured environment reviewers and PyPI OIDC trusted publishing.

## Why this project

MCP local servers run as ordinary processes with their launcher's privileges;
configuration review is a useful point to inspect what will be trusted.
[MCP security guidance](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/SECURITY.md)
documents that trust model. Existing tools such as
[Snyk Agent Scan](https://github.com/snyk/agent-scan#security-warning) provide
broader runtime/catalog analysis and may launch servers or contact endpoints.
This project's narrow scope is a small, deterministic, offline review before launch.

[Topic decision](research/TOPIC_REPORT.md) · [Plan](PLAN.md) · [MIT license](LICENSE)
