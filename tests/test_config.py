from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_config_audit.config import MAX_INPUT_BYTES, ConfigError, load_config, parse_config


class ConfigTests(unittest.TestCase):
    def test_three_supported_schemas(self) -> None:
        server = {"local": {"command": "python", "args": ["server.py"]}}
        for data in ({"mcpServers": server}, {"servers": server}, {"mcp": {"servers": server}}):
            with self.subTest(data=data):
                self.assertEqual(parse_config(json.dumps(data).encode()).servers, server)

    def test_jsonc_strings_and_escaped_quotes(self) -> None:
        raw = rb"""{/* comment */ "servers": {"a": {"url": "https://example.com//path?quote=\"x\"",},},}"""
        self.assertIn("//path", parse_config(raw).servers["a"]["url"])

    def test_bom_and_comments(self) -> None:
        self.assertEqual(parse_config(b'\xef\xbb\xbf{"servers": {}} // end').servers, {})

    def test_invalid_inputs_fail_without_echo(self) -> None:
        invalid = [
            b'{"secret": "DO_NOT_ECHO",}',
            b"[]",
            b"{",
            b"\xff",
            b"/*oops",
            b'{"servers":[],"mcpServers":{}}',
            b'{"servers":[]}',
            b'{"servers":{"x":null}}',
            b'{"servers":{"x":{}}}',
            b'{"servers":{"x":{"command":5}}}',
            b'{"servers":{"x":{"command":"x","args":"x"}}}',
            b'{"servers":{"x":{"command":"x","env":{"X":5}}}}',
            b'{"servers":{"x":{"command":"x","disabled":"false"}}}',
            b'{"servers":{"x":{"command":"x","url":"https://example.com"}}}',
            b'{"servers":{},"servers":{}}',
            b"[" * 3000,
            b" " * (MAX_INPUT_BYTES + 1),
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:60]):
                with self.assertRaises(ConfigError) as caught:
                    parse_config(raw)
                self.assertNotIn("DO_NOT_ECHO", str(caught.exception))

    def test_missing_path_sanitizes_error(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            load_config(Path("missing-DO_NOT_ECHO.json"))
        self.assertNotIn("DO_NOT_ECHO", str(caught.exception))

    def test_digest_is_exact_input(self) -> None:
        self.assertNotEqual(parse_config(b'{"servers":{}}').digest, parse_config(b'{"servers":{ }}').digest)


if __name__ == "__main__":
    unittest.main()
