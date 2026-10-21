from __future__ import annotations

import json
import unittest

from agent_config_audit.compare import compare
from agent_config_audit.config import parse_config
from agent_config_audit.reports import fails, make_report, render


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = parse_config(
            json.dumps(
                {
                    "servers": {
                        "<script>alert(1)</script>": {
                            "command": "bash",
                            "env": {"API_TOKEN": "DO_NOT_LEAK_12345"},
                        }
                    }
                }
            ).encode()
        )

    def test_all_formats_redact_values(self) -> None:
        for format_name in ("text", "json", "sarif", "html"):
            with self.subTest(format_name=format_name):
                text = render(make_report(self.config), format_name)
                self.assertNotIn("DO_NOT_LEAK_12345", text)

    def test_html_escapes_server_and_pointer(self) -> None:
        text = render(make_report(self.config), "html")
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("default-src 'none'", text)

    def test_terminal_controls_removed(self) -> None:
        data = parse_config(b'{"servers":{"\\u001b[31m\\nINJECT":{"command":"bash"}}}')
        self.assertNotIn("\x1b", render(make_report(data), "text"))
        self.assertNotIn("\nINJECT", render(make_report(data), "text"))

    def test_deterministic(self) -> None:
        for format_name in ("text", "json", "sarif", "html"):
            self.assertEqual(
                render(make_report(self.config), format_name), render(make_report(self.config), format_name)
            )

    def test_sarif_schema_shape(self) -> None:
        result = json.loads(render(make_report(self.config), "sarif"))
        self.assertEqual(result["version"], "2.1.0")
        self.assertEqual(len(result["runs"][0]["tool"]["driver"]["rules"]), 12)
        self.assertTrue(result["runs"][0]["results"][0]["properties"]["jsonPointer"].startswith("/servers/"))

    def test_thresholds(self) -> None:
        report = make_report(self.config)
        for level in ("high", "medium", "low"):
            self.assertTrue(fails(report, level))
        self.assertFalse(fails(report, "none"))

    def test_diff_categories_and_no_secret_values(self) -> None:
        before = parse_config(b'{"servers":{"a":{"command":"server","env":{"TOKEN":"old"}},"gone":{"command":"x"}}}')
        after = parse_config(
            b'{"servers":{"a":{"command":"server","env":{"TOKEN":"new-secret"}},"new":{"command":"x"}}}'
        )
        changes = compare(before, after)
        self.assertEqual(
            [(c.server, c.kind) for c in changes], [("a", "changed"), ("gone", "removed"), ("new", "added")]
        )
        self.assertEqual(changes[0].fields, ["env"])
        for format_name in ("text", "json", "html", "sarif"):
            self.assertNotIn("new-secret", render(make_report(after, before), format_name))

    def test_diff_no_change_and_disabled_change(self) -> None:
        self.assertEqual(compare(self.config, self.config), [])
        before = parse_config(b'{"servers":{"a":{"command":"bash","disabled":true}}}')
        after = parse_config(b'{"servers":{"a":{"command":"bash","disabled":false}}}')
        self.assertEqual(compare(before, after)[0].fields, ["disabled"])
        self.assertEqual(make_report(after, before)["before_findings"], [])
