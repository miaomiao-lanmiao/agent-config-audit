"""Explicit-path CLI with stable exit codes and safe output handling."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .reports import fails, make_report, render


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-config-audit",
        description="Offline static preflight for MCP JSON/JSONC configurations. Never starts servers.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("scan", "diff"):
        sub = commands.add_parser(command, help="Review a config" if command == "scan" else "Compare config revisions")
        if command == "diff":
            sub.add_argument("before", type=Path)
        sub.add_argument("config", type=Path)
        sub.add_argument("--format", choices=["text", "json", "html", "sarif"], default="text")
        sub.add_argument("--output", "-o", type=Path, help="Create a new output file; never overwrite existing files")
        sub.add_argument(
            "--fail-on",
            choices=["high", "medium", "low", "none"],
            default=os.environ.get("ACA_FAIL_ON", "high"),
            help="CI threshold (default: high or ACA_FAIL_ON)",
        )
        sub.add_argument("--fail-on-change", action="store_true", help="Diff: also fail on any configuration change")
    args = parser.parse_args(argv)
    if args.fail_on not in {"high", "medium", "low", "none"}:
        parser.error("ACA_FAIL_ON must be high, medium, low, or none")
    if args.fail_on_change and args.command != "diff":
        parser.error("--fail-on-change requires diff")
    try:
        config = load_config(args.config)
        before = load_config(args.before) if args.command == "diff" else None
        report = make_report(config, before)
        output = render(report, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output)
        else:
            sys.stdout.write(output)
        changed = bool(report.get("changes")) and args.fail_on_change
        return 1 if fails(report, args.fail_on) or changed else 0
    except (ConfigError, OSError, UnicodeError) as exc:
        message = str(exc) if isinstance(exc, ConfigError) else "Cannot write output; choose a new writable path."
        print(f"agent-config-audit: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
