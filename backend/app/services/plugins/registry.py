"""Plugin registry: records and lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import ModuleType

from app.services.plugins.context import PluginContext
from app.services.plugins.errors import PluginNotFoundError
from app.services.plugins.manifest import PluginManifest


class PluginState(StrEnum):
    """Lifecycle state of a plugin."""

    DISCOVERED = "discovered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginRecord:
    """Tracks a single plugin through its lifecycle."""

    name: str
    path: Path
    manifest: PluginManifest | None = None
    state: PluginState = PluginState.DISCOVERED
    module: ModuleType | None = None
    context: PluginContext | None = None
    error: str | None = None


class PluginRegistry:
    """Name-indexed collection of plugin records, preserving insertion order."""

    def __init__(self) -> None:
        self._records: dict[str, PluginRecord] = {}

    def add(self, record: PluginRecord) -> None:
        self._records[record.name] = record

    def get(self, name: str) -> PluginRecord:
        try:
            return self._records[name]
        except KeyError:
            raise PluginNotFoundError(f"Plugin '{name}' is not registered") from None

    def has(self, name: str) -> bool:
        return name in self._records

    def remove(self, name: str) -> None:
        self._records.pop(name, None)

    def all(self) -> list[PluginRecord]:
        return list(self._records.values())

    def names(self) -> list[str]:
        return list(self._records)
