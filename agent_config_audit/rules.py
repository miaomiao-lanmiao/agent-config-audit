"""Heuristics over configuration data, never over running MCP servers."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from .config import Config, pointer_token

SEVERITY = {"low": 1, "medium": 2, "high": 3}
RULES: dict[str, tuple[str, str, str]] = {
    "ACA001": (
        "high",
        "Inline credential",
        "Replace literal secrets with your client's supported environment or secret-input reference.",
    ),
    "ACA002": (
        "medium",
        "Unpinned package launch",
        "Use an exact package version and review the package provenance before launch.",
    ),
    "ACA003": (
        "high",
        "Shell interpreter launch",
        "Prefer a reviewed executable with an explicit argument array; inspect any shell script manually.",
    ),
    "ACA004": (
        "high",
        "Broad filesystem scope",
        "Grant only a dedicated project directory instead of a root or entire home directory.",
    ),
    "ACA005": (
        "high",
        "Privileged container",
        "Remove privileged mode and use the smallest set of container permissions.",
    ),
    "ACA006": (
        "high",
        "Sensitive container mount",
        "Avoid host roots, home directories and container engine sockets; mount only task data.",
    ),
    "ACA007": ("high", "Unencrypted remote transport", "Use HTTPS for remote MCP endpoints and authenticate access."),
    "ACA008": (
        "high",
        "TLS verification disabled",
        "Restore certificate verification and configure trusted CA certificates.",
    ),
    "ACA009": (
        "medium",
        "Automatic package confirmation",
        "Review package installation explicitly or preinstall an audited, pinned package.",
    ),
    "ACA010": (
        "medium",
        "Credential-bearing URL",
        "Move URL credentials and query authentication into supported secret references.",
    ),
    "ACA011": (
        "medium",
        "Plain HTTP loopback",
        "Review local service authentication and origin validation; loopback alone is not an access boundary.",
    ),
    "ACA012": (
        "medium",
        "Remote URL needs review",
        "Use an absolute HTTP(S) endpoint without interpolation and review its destination.",
    ),
}
SECRET_KEY = re.compile(
    r"(?:token|secret|password|passwd|api[_-]?key|authorization|credential|cookie|private[_-]?key)", re.I
)
REFERENCE = re.compile(r"^(?:\$\{[^{}]+\}|\$[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*%)$")
PLACEHOLDERS = {"", "example", "changeme", "your-token", "your-api-key", "redacted", "<redacted>"}
EXACT_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    server: str
    pointer: str
    title: str
    recommendation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def is_literal(value: str) -> bool:
    value = value.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value.lower() not in PLACEHOLDERS and not REFERENCE.fullmatch(value)


def broad_path(value: str) -> bool:
    if not value.strip():
        return False
    path = value.strip().replace("\\", "/").rstrip("/").casefold()
    return path in {
        "",
        "~",
        "$home",
        "${home}",
        "%userprofile%",
        "${env:home}",
        "${env:userprofile}",
        "/home",
        "/users",
        "/root",
        "/mnt",
        "/host",
    } or bool(re.fullmatch(r"[a-z]:|/(?:home|users)/[^/]+|[a-z]:/users/[^/]+", path))


def _package_pinned(command: str, args: list[str]) -> bool:
    """Conservatively recognize exact versions for npx/uvx common forms."""
    if command in {"npx", "npx.cmd", "npm", "npm.cmd"}:
        packages: list[str] = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in {"-p", "--package"}:
                if i + 1 >= len(args):
                    return False
                packages.append(args[i + 1])
                i += 2
                continue
            if arg.startswith("--package="):
                packages.append(arg.split("=", 1)[1])
            elif arg in {"--", "exec", "x"} or arg.startswith("-"):
                pass
            else:
                if not packages:
                    packages.append(arg)
                break
            i += 1
        return bool(packages) and all(
            bool(EXACT_VERSION.fullmatch(package.rsplit("@", 1)[-1])) and "@" in package.lstrip("@")
            for package in packages
        )
    if command in {"uvx", "uvx.exe"}:
        if any(arg.startswith(("--from", "--with")) for arg in args):
            return False  # Multiple resolution sources require manual review.
        package = next((arg for arg in args if not arg.startswith("-")), "")
        return "==" in package and bool(EXACT_VERSION.fullmatch(package.split("==", 1)[1]))
    return True


def _recorder(findings: list[Finding], name: str, base: str) -> Callable[[str, str], None]:
    """Bind server identity and deduplicate each rule within this server."""
    seen: set[str] = set()

    def add(rule: str, field: str) -> None:
        if rule not in seen:
            seen.add(rule)
            severity, title, fix = RULES[rule]
            findings.append(Finding(rule, severity, name, f"{base}/{field}", title, fix))

    return add


def audit(config: Config) -> list[Finding]:
    findings: list[Finding] = []
    for name, server in sorted(config.servers.items()):
        if server.get("disabled", False):
            continue
        add = _recorder(findings, name, f"{config.pointer}/{pointer_token(name)}")

        for field in ("env", "headers"):
            values = server.get(field, {})
            if any(SECRET_KEY.search(key) and is_literal(value) for key, value in values.items()):
                add("ACA001", field)
        args = server.get("args", [])
        for i, arg in enumerate(args):
            key, separator, value = arg.partition("=")
            if separator and SECRET_KEY.search(key) and is_literal(value):
                add("ACA001", f"args/{i}")
            if SECRET_KEY.search(arg) and arg.startswith("-") and not separator and i + 1 < len(args):
                if is_literal(args[i + 1]):
                    add("ACA001", f"args/{i + 1}")
        command = server.get("command", "").replace("\\", "/").rsplit("/", 1)[-1].lower()
        command = command.removesuffix(".exe").removesuffix(".cmd")
        if command in {
            "sh",
            "bash",
            "zsh",
            "fish",
            "cmd",
            "cmd.exe",
            "powershell",
            "powershell.exe",
            "pwsh",
            "pwsh.exe",
        }:
            add("ACA003", "command")
        package_launcher = command in {"npx", "uvx"} or (command == "npm" and bool(args) and args[0] in {"exec", "x"})
        if package_launcher:
            if not _package_pinned(command, args):
                add("ACA002", "args")
            if any(arg in {"-y", "--yes"} or arg.startswith("--yes=") for arg in args):
                add("ACA009", "args")
        for i, arg in enumerate(args):
            path_arg = arg.partition("=")[2] if arg.startswith("-") and "=" in arg else arg
            if not path_arg.startswith("-") and broad_path(path_arg):
                add("ACA004", f"args/{i}")
        if command in {"docker", "docker.exe", "podman", "podman.exe"}:
            if "--privileged" in args or any(arg.lower() == "--privileged=true" for arg in args):
                add("ACA005", "args")
            for i, arg in enumerate(args):
                mount = ""
                if arg in {"-v", "--volume", "--mount"} and i + 1 < len(args):
                    mount = args[i + 1]
                elif arg.startswith(("--volume=", "--mount=")):
                    mount = arg.split("=", 1)[1]
                elif arg.startswith("-v") and len(arg) > 2:
                    mount = arg[2:]
                if mount:
                    source_match = re.search(r"(?:^|,)(?:source|src)=([^,]+)", mount)
                    drive = bool(re.match(r"^[A-Za-z]:[/\\]", mount))
                    separator = mount.find(":", 2 if drive else 0)
                    source = source_match[1] if source_match else mount[:separator] if separator >= 0 else mount
                    if broad_path(source) or "docker.sock" in mount or "podman.sock" in mount:
                        add("ACA006", "args")
        env: dict[str, str] = server.get("env", {})
        if any(
            (key.upper() in {"NODE_TLS_REJECT_UNAUTHORIZED", "PYTHONHTTPSVERIFY"} and value == "0")
            or (key.upper() in {"GIT_SSL_NO_VERIFY"} and value.lower() in {"1", "true", "yes"})
            for key, value in env.items()
        ):
            add("ACA008", "env")
        if any(arg in {"--insecure", "--ignore-certificate-errors"} for arg in args):
            add("ACA008", "args")
        if "url" in server:
            _audit_url(server, add)
    return sorted(findings, key=lambda item: (-SEVERITY[item.severity], item.server, item.rule_id))


def _audit_url(server: dict[str, Any], add: Callable[[str, str], None]) -> None:
    raw = server["url"]
    if any(ord(char) < 32 or ord(char) == 127 for char in raw):
        add("ACA012", "url")
    try:
        url = urlsplit(raw)
        host = (url.hostname or "").lower()
        _ = url.port
    except ValueError:
        add("ACA012", "url")
        return
    if url.scheme not in {"http", "https"} or not host or re.search(r"[\s${}%]", host):
        add("ACA012", "url")
    if url.scheme == "http":
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host == "localhost"
        add("ACA011" if loopback else "ACA007", "url")
    if (
        url.username
        or url.password
        or any(SECRET_KEY.search(key) for key, _ in parse_qsl(url.query, keep_blank_values=True))
    ):
        add("ACA010", "url")
