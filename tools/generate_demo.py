"""Create only known synthetic demo artifacts, never inspect personal config."""

from __future__ import annotations

import json
from pathlib import Path

from agent_config_audit.config import load_config, parse_config
from agent_config_audit.reports import make_report, render


def main() -> None:
    output = Path("reports")
    output.mkdir(exist_ok=True)
    risky = load_config(Path("examples/risky.json"))
    hardened = load_config(Path("examples/hardened.json"))
    xss = parse_config(json.dumps({"servers": {"<script>alert(1)</script>": {"command": "bash"}}}).encode())
    reports = {
        "risky": make_report(risky),
        "hardened": make_report(hardened),
        "diff": make_report(hardened, risky),
        "xss": make_report(xss),
    }
    for name, report in reports.items():
        for format_name in ("html", "json", "sarif", "text"):
            extension = "txt" if format_name == "text" else format_name
            (output / f"{name}.{extension}").write_text(render(report, format_name), encoding="utf-8")
    print("Synthetic demo reports generated in reports/.")


if __name__ == "__main__":
    main()
