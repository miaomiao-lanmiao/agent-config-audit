# Contributing

Open an issue describing a reproducible configuration-review need. Use synthetic
values. Include the Python version, operating system, tool version and rule ID.

For a rule change, add positive, negative and evasion/edge cases. Document false
positives and scope in `docs/RULES.md`. Do not add network lookups or execution to
the scanner. Keep findings deterministic and output values redacted.

Run the development checks in README.md before submitting a pull request. Use
conventional commit titles, explain changed behavior and include verification
results. For report layout changes, attach desktop/mobile local screenshots that
contain no private information. Reviewers merge manually.
