"""Strict configuration loading. No discovery, interpolation or execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 2 * 1024 * 1024


class ConfigError(ValueError):
    """An input cannot be safely interpreted as a supported configuration."""


@dataclass(frozen=True)
class Config:
    servers: dict[str, dict[str, Any]]
    pointer: str
    digest: str


def _jsonc(text: str) -> str:
    """Blank comments and trailing commas without touching JSON strings."""
    chars = list(text)
    i, quoted, escaped = 0, False, False
    while i < len(chars):
        char = chars[i]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            i += 1
            continue
        if char == '"':
            quoted = True
        elif text[i : i + 2] == "//":
            while i < len(chars) and chars[i] not in "\r\n":
                chars[i] = " "
                i += 1
            continue
        elif text[i : i + 2] == "/*":
            end = text.find("*/", i + 2)
            if end < 0:
                raise ConfigError("Unterminated JSONC comment.")
            for index in range(i, end + 2):
                if chars[index] not in "\r\n":
                    chars[index] = " "
            i = end + 2
            continue
        i += 1
    quoted, escaped = False, False
    for i, char in enumerate(chars):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == ",":
            j = i + 1
            while j < len(chars) and chars[j].isspace():
                j += 1
            if j < len(chars) and chars[j] in "}]":
                chars[i] = " "
    return "".join(chars)


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("Duplicate JSON keys are ambiguous; remove duplicates.")
        result[key] = value
    return result


def parse_config(raw: bytes) -> Config:
    if len(raw) > MAX_INPUT_BYTES:
        raise ConfigError("Configuration exceeds the 2 MiB input limit.")
    try:
        data = json.loads(_jsonc(raw.decode("utf-8-sig")), object_pairs_hook=_unique)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ConfigError("Invalid UTF-8 JSON/JSONC configuration; check its syntax.") from exc
    if not isinstance(data, dict):
        raise ConfigError("The configuration root must be an object.")
    candidates: list[tuple[str, Any]] = []
    for key in ("mcpServers", "servers"):
        if key in data:
            candidates.append((f"/{key}", data[key]))
    if isinstance(data.get("mcp"), dict) and "servers" in data["mcp"]:
        candidates.append(("/mcp/servers", data["mcp"]["servers"]))
    if len(candidates) != 1:
        raise ConfigError("Provide exactly one of mcpServers, servers, or mcp.servers.")
    pointer, servers = candidates[0]
    if not isinstance(servers, dict):
        raise ConfigError("The servers collection must be an object.")
    for name, server in servers.items():
        if not isinstance(name, str) or not name or not isinstance(server, dict):
            raise ConfigError("Each named server must be a nonempty object entry.")
        for key in ("command", "url", "type", "cwd"):
            if key in server and not isinstance(server[key], str):
                raise ConfigError("Server command/url/type/cwd fields must be strings.")
        for key in ("disabled",):
            if key in server and not isinstance(server[key], bool):
                raise ConfigError("Server disabled must be a boolean.")
        if "args" in server and (
            not isinstance(server["args"], list) or not all(isinstance(arg, str) for arg in server["args"])
        ):
            raise ConfigError("Server args must be an array of strings.")
        for key in ("env", "headers"):
            if key in server and (
                not isinstance(server[key], dict) or not all(isinstance(value, str) for value in server[key].values())
            ):
                raise ConfigError("Server env/headers must map names to string values.")
        if not server.get("command") and not server.get("url"):
            raise ConfigError("Each server requires a nonempty command or URL.")
        if server.get("command") and server.get("url"):
            raise ConfigError("A server cannot declare both command and URL.")
    return Config(servers, pointer, hashlib.sha256(raw).hexdigest())


def load_config(path: Path) -> Config:
    try:
        with path.open("rb") as stream:
            return parse_config(stream.read(MAX_INPUT_BYTES + 1))
    except OSError as exc:
        raise ConfigError("Cannot read the requested configuration file.") from exc


def pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
