"""Plugin manifest model, permissions, and version compatibility helpers."""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

_VERSION_RE = re.compile(r"^\d+(\.\d+){0,2}$")


class PluginPermission(StrEnum):
    """Capabilities a plugin may request in its manifest."""

    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    CLIPBOARD = "clipboard"
    NETWORK = "network"
    NOTIFICATIONS = "notifications"
    TOOL_ACCESS = "tool_access"
    SETTINGS_ACCESS = "settings_access"


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a ``major[.minor[.patch]]`` string into a 3-tuple."""
    if not _VERSION_RE.match(version):
        raise ValueError(f"Invalid version string: '{version}'")
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def version_satisfies(current: str, minimum: str) -> bool:
    """Return whether ``current`` >= ``minimum`` (semantic-ish comparison)."""
    return parse_version(current) >= parse_version(minimum)


class PluginManifest(BaseModel):
    """Validated contents of a plugin's ``plugin.json``."""

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", max_length=64)
    version: str = Field(default="0.1.0")
    author: str = Field(default="", max_length=128)
    description: str = Field(default="", max_length=512)
    permissions: list[PluginPermission] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    min_exo_version: str | None = None
    entry_point: str = Field(default="register")
    enabled_by_default: bool = True

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        parse_version(value)  # raises ValueError if malformed
        return value

    @field_validator("min_exo_version")
    @classmethod
    def _validate_min_version(cls, value: str | None) -> str | None:
        if value is not None:
            parse_version(value)
        return value

    def is_compatible_with(self, exo_version: str) -> bool:
        """Whether this plugin can run against the given EXO version."""
        if self.min_exo_version is None:
            return True
        return version_satisfies(exo_version, self.min_exo_version)

    def has_permission(self, permission: PluginPermission) -> bool:
        return permission in self.permissions
