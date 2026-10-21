# Security policy

## Scope and supported version

0.1.x is the supported alpha line. This tool reviews explicit configuration data;
it does not sandbox MCP servers, verify package behavior or detect all secrets.
No findings is not a security guarantee. See the rule reference for limitations.

## Reporting

Use the repository's **Security → Report a vulnerability** private reporting
feature if enabled. If unavailable, open a public issue requesting a private
reporting channel without including exploit details, secrets or personal config.
Maintainers should enable private vulnerability reporting before release.

Report input-triggered execution/network access, raw secret-value disclosure,
HTML injection or unsafe file overwrite behavior with a minimal synthetic
fixture. Do not attach real credentials or full personal configuration files.

Server names and JSON pointers are intentionally included in reports. Put no
credentials in those identifiers and review reports before sharing. SHA-256
digests identify input bytes; they are not proofs that a configuration is safe.
