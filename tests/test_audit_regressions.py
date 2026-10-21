"""Release audit regressions from adversarial, synthetic configuration data."""

from __future__ import annotations

import json
import unittest

from agent_config_audit.config import ConfigError, parse_config
from agent_config_audit.rules import audit
from tools.release_preflight import validate_branches, validate_environment


def rule_ids(server: dict[str, object]) -> set[str]:
    config = parse_config(json.dumps({"servers": {"audit": server}}).encode())
    return {item.rule_id for item in audit(config)}


class ReleaseAuditTests(unittest.TestCase):
    def test_nonfinite_json_is_rejected(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), self.assertRaises(ConfigError):
                parse_config(('{"servers":{},"metadata":' + constant + "}").encode())

    def test_huge_integer_returns_safe_config_error(self) -> None:
        with self.assertRaises(ConfigError):
            parse_config(b'{"servers":{},"metadata":' + b"9" * 5000 + b"}")

    def test_empty_value_before_trailing_comma_is_rejected(self) -> None:
        for raw in (b'{"servers":{,}}', b'{"servers":{"x":{"command":"x","args":[,]}}}'):
            with self.subTest(raw=raw), self.assertRaises(ConfigError):
                parse_config(raw)

    def test_windows_launchers_have_the_same_rules(self) -> None:
        for command in ("npx.exe", "npm.exe", "uvx.cmd"):
            args = ["exec", "pkg@latest"] if command == "npm.exe" else ["pkg"]
            with self.subTest(command=command):
                self.assertIn("ACA002", rule_ids({"command": command, "args": args}))

    def test_npm_local_script_is_not_a_package_install(self) -> None:
        self.assertNotIn("ACA002", rule_ids({"command": "npm", "args": ["run", "server"]}))

    def test_assignment_style_root_scope(self) -> None:
        for arg in ("--directory=/", "--path=C:\\", "--root=${HOME}"):
            with self.subTest(arg=arg):
                self.assertIn("ACA004", rule_ids({"command": "server", "args": [arg]}))
        self.assertNotIn("ACA004", rule_ids({"command": "server", "args": ["--directory=/srv/project"]}))

    def test_percent_encoded_query_credentials(self) -> None:
        self.assertIn("ACA010", rule_ids({"url": "https://example.com/mcp?%61pi%5fkey=synthetic"}))

    def test_url_controls_require_review(self) -> None:
        self.assertIn("ACA012", rule_ids({"url": "https://exam\nple.com/mcp"}))

    def test_malformed_release_metadata_fails_closed(self) -> None:
        for data in ({"deployment_branch_policy": []}, {"deployment_branch_policy": "invalid"}):
            self.assertTrue(validate_environment(data))
        for data in ({"branch_policies": [None]}, {"branch_policies": "main"}):
            self.assertTrue(validate_branches(data))
