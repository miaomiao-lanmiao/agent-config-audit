from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from agent_config_audit.config import load_config, parse_config
from agent_config_audit.rules import audit


def config(server: dict[str, object]) -> bytes:
    return json.dumps({"mcpServers": {"test": server}}).encode()


def codes(server: dict[str, object]) -> set[str]:
    return {item.rule_id for item in audit(parse_config(config(server)))}


class RulesTests(unittest.TestCase):
    def test_inline_credentials(self) -> None:
        for field in ("env", "headers"):
            self.assertIn("ACA001", codes({"command": "server", field: {"API_KEY": "private-literal"}}))

    def test_references_not_literals(self) -> None:
        for value in ("${env:KEY}", "${input:key}", "$KEY", "%KEY%", "Bearer ${env:KEY}", "", "changeme"):
            with self.subTest(value=value):
                self.assertNotIn("ACA001", codes({"command": "server", "env": {"API_TOKEN": value}}))

    def test_nonsecret_env(self) -> None:
        self.assertEqual(codes({"command": "server", "env": {"LOG_LEVEL": "info"}}), set())

    def test_arg_secrets(self) -> None:
        for args in (["--api-key=literal"], ["--token", "literal"]):
            self.assertIn("ACA001", codes({"command": "server", "args": args}))

    def test_npx_mutable_and_fixed(self) -> None:
        for package in ("package", "package@latest", "@scope/pkg", "pkg@^1.2.3", "pkg@1.2.x"):
            with self.subTest(package=package):
                self.assertIn("ACA002", codes({"command": "npx", "args": [package]}))
        for args in (
            ["pkg@1.2.3"],
            ["@scope/pkg@1.2.3"],
            ["--package", "pkg@1.2.3", "--", "bin"],
            ["--package=pkg@1.2.3", "bin"],
        ):
            with self.subTest(args=args):
                self.assertNotIn("ACA002", codes({"command": "npx", "args": args}))

    def test_uvx_version(self) -> None:
        self.assertNotIn("ACA002", codes({"command": "uvx", "args": ["pkg==1.2.3"]}))
        self.assertIn("ACA002", codes({"command": "uvx", "args": ["pkg"]}))

    def test_shells(self) -> None:
        for command in ("bash", "sh", "cmd.exe", "pwsh", r"C:\Windows\System32\cmd.exe"):
            self.assertIn("ACA003", codes({"command": command, "args": ["-c", "echo test"]}))

    def test_broad_roots_and_home(self) -> None:
        for folder in ("/", "C:\\", "~", "${HOME}", "${env:USERPROFILE}", "/home/person", "C:/Users/person"):
            with self.subTest(folder=folder):
                self.assertIn("ACA004", codes({"command": "server", "args": [folder]}))
        self.assertNotIn("ACA004", codes({"command": "server", "args": ["/srv/project/data"]}))

    def test_privileged_container(self) -> None:
        for flag in ("--privileged", "--privileged=true"):
            self.assertIn("ACA005", codes({"command": "docker", "args": ["run", flag, "image"]}))
        self.assertNotIn("ACA005", codes({"command": "docker", "args": ["run", "--privileged=false", "image"]}))

    def test_docker_mount_syntaxes(self) -> None:
        variants = [
            ["-v", "/:/host"],
            ["--mount", "type=bind,source=/,target=/host"],
            ["--volume=/var/run/docker.sock:/var/run/docker.sock"],
            ["-vC:\\:/host"],
        ]
        for args in variants:
            with self.subTest(args=args):
                self.assertIn("ACA006", codes({"command": "docker", "args": ["run", *args, "image"]}))
        self.assertNotIn("ACA006", codes({"command": "docker", "args": ["run", "-v", "/srv/data:/data", "image"]}))

    def test_remote_http(self) -> None:
        self.assertIn("ACA007", codes({"url": "http://example.com/mcp"}))
        self.assertNotIn("ACA007", codes({"url": "https://example.com/mcp"}))

    def test_tls_disable(self) -> None:
        for env in ({"NODE_TLS_REJECT_UNAUTHORIZED": "0"}, {"PYTHONHTTPSVERIFY": "0"}, {"GIT_SSL_NO_VERIFY": "true"}):
            self.assertIn("ACA008", codes({"command": "server", "env": env}))

    def test_auto_confirm(self) -> None:
        self.assertIn("ACA009", codes({"command": "npx", "args": ["-y", "pkg@1.2.3"]}))

    def test_url_credentials_and_localhost(self) -> None:
        self.assertIn("ACA010", codes({"url": "https://user:password@example.com/mcp"}))
        self.assertIn("ACA010", codes({"url": "https://example.com/mcp?api_key=demo"}))
        for url in ("http://127.0.0.1/mcp", "http://[::1]/mcp", "http://localhost/mcp"):
            self.assertIn("ACA011", codes({"url": url}))

    def test_malformed_url(self) -> None:
        for url in (
            "file:///etc/passwd",
            "https://[oops",
            "https://example.com:bad",
            "${env:MCP_URL}",
            "https://${env:HOST}/mcp",
        ):
            with self.subTest(url=url):
                self.assertIn("ACA012", codes({"url": url}))

    def test_disabled_skipped(self) -> None:
        self.assertEqual(codes({"command": "bash", "disabled": True}), set())

    def test_scanner_never_starts_or_connects(self) -> None:
        with (
            patch("subprocess.Popen", side_effect=AssertionError("process started")),
            patch("socket.socket", side_effect=AssertionError("network opened")),
        ):
            self.assertIn("ACA003", codes({"command": "bash", "args": ["-c", "NEVER_RUN"]}))

    def test_fixtures(self) -> None:
        from pathlib import Path

        self.assertEqual(len(audit(load_config(Path("examples/risky.json")))), 8)
        self.assertEqual(audit(load_config(Path("examples/hardened.json"))), [])
        self.assertEqual(audit(load_config(Path("examples/vscode.jsonc"))), [])
