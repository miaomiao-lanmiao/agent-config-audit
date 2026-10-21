"""Configuration drift described by field categories, never raw values."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import Config


@dataclass(frozen=True)
class Change:
    server: str
    kind: str
    fields: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compare(before: Config, after: Config) -> list[Change]:
    changes = []
    known = {"command", "args", "url", "env", "headers", "type", "disabled", "cwd"}
    for name in sorted(before.servers.keys() | after.servers.keys()):
        if name not in before.servers:
            changes.append(Change(name, "added", []))
        elif name not in after.servers:
            changes.append(Change(name, "removed", []))
        else:
            old, new = before.servers[name], after.servers[name]
            keys = old.keys() | new.keys()
            fields = sorted(
                {
                    key if key in known else "other"
                    for key in keys
                    if (key in old) != (key in new) or old.get(key) != new.get(key)
                }
            )
            if fields:
                changes.append(Change(name, "changed", fields))
    return changes
