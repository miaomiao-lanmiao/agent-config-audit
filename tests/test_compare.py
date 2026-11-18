from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from agent_config_audit.cli import main
from agent_config_audit.compare import Change, compare
from agent_config_audit.config import Config, parse_config


def config(value: Any) -> Config:
    return parse_config(json.dumps({"servers": {"demo": {"command": "synthetic-server", "extension": value}}}).encode())


class CompareTests(unittest.TestCase):
    def test_boolean_and_number_changes_at_each_nesting_level(self) -> None:
        for boolean, number in ((False, 0), (True, 1), (False, 0.0), (True, 1.0)):
            for old, new in ((boolean, number), (number, boolean)):
                for before, after in ((old, new), ({"flag": old}, {"flag": new}), ([{"flag": old}], [{"flag": new}])):
                    with self.subTest(before=before, after=after):
                        self.assertEqual(compare(config(before), config(after)), [Change("demo", "changed", ["other"])])

    def test_object_order_and_equivalent_numbers_are_unchanged(self) -> None:
        before = config({"first": [1, False, None], "second": {"value": 0.0}})
        after = config({"second": {"value": 0}, "first": [1.0, False, None]})
        self.assertEqual(compare(before, after), [])

    def test_array_order_container_types_and_missing_null_are_changes(self) -> None:
        for before, after in (([1, 2], [2, 1]), ({}, []), ({"flag": None}, {})):
            with self.subTest(before=before, after=after):
                self.assertEqual(compare(config(before), config(after)), [Change("demo", "changed", ["other"])])

    def test_deeply_nested_boolean_change(self) -> None:
        before: Any = True
        after: Any = 1
        for _ in range(200):
            before, after = [before], [after]
        self.assertEqual(compare(config(before), config(after)), [Change("demo", "changed", ["other"])])

    def test_cli_gates_type_changes_without_exposing_values(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            before = root / "before.json"
            after = root / "after.json"
            for path, value in ((before, True), (after, 1)):
                path.write_text(
                    json.dumps(
                        {"servers": {"demo": {
                            "command": "synthetic-private-launcher",
                            "private-extension": {"allow": value, "secret": "SYNTHETIC_DO_NOT_EXPORT"},
                        }}}
                    ),
                    encoding="utf-8",
                )
            for format_name in ("json", "text", "html", "sarif"):
                with self.subTest(format_name=format_name):
                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        code = main(
                            [
                                "diff", str(before), str(after), "--fail-on", "none",
                                "--fail-on-change", "--format", format_name,
                            ]
                        )
                    self.assertEqual(code, 1)
                    self.assertEqual(err.getvalue(), "")
                    report = out.getvalue()
                    self.assertIn("other", report)
                    for private in ("SYNTHETIC_DO_NOT_EXPORT", "synthetic-private-launcher", "private-extension"):
                        self.assertNotIn(private, report)
