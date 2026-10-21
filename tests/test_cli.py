from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {key: value for key, value in os.environ.items() if key != "ACA_FAIL_ON"}
        return subprocess.run(
            [sys.executable, "-m", "agent_config_audit", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def test_help_and_version(self) -> None:
        self.assertEqual(self.run_cli("--help").returncode, 0)
        self.assertEqual(self.run_cli("--version").stdout.strip(), "0.1.0")

    def test_scan_statuses(self) -> None:
        for file, code in (("hardened.json", 0), ("risky.json", 1), ("missing.json", 2)):
            self.assertEqual(self.run_cli("scan", "examples/" + file).returncode, code)

    def test_json_and_threshold(self) -> None:
        result = self.run_cli("scan", "examples/risky.json", "--format", "json", "--fail-on", "none")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["summary"]["findings"], 8)

    def test_existing_output_and_input_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "existing.json"
            target.write_text("PRESERVE", encoding="utf-8")
            result = self.run_cli("scan", "examples/hardened.json", "-o", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_text(), "PRESERVE")
        original = Path("examples/hardened.json").read_bytes()
        self.assertEqual(self.run_cli("scan", "examples/hardened.json", "-o", "examples/hardened.json").returncode, 2)
        self.assertEqual(Path("examples/hardened.json").read_bytes(), original)

    def test_diff_fail_on_change(self) -> None:
        result = self.run_cli("diff", "examples/risky.json", "examples/hardened.json", "--fail-on-change")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            self.run_cli("diff", "examples/hardened.json", "examples/hardened.json", "--fail-on-change").returncode, 0
        )

    def test_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "nested" / "report.json"
            self.assertEqual(
                self.run_cli("scan", "examples/hardened.json", "--format", "json", "-o", str(target)).returncode, 0
            )
            self.assertEqual(json.loads(target.read_text())["summary"]["findings"], 0)
