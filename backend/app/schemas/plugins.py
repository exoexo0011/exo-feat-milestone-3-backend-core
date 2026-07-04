"""Schemas for the plugins REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.plugins.context import Command, SettingsPage, UiPanel
from app.services.plugins.registry import PluginRecord


class PluginInfo(BaseModel):
    """Public view of a plugin record."""

    name: str
    state: str
    version: str
    author: str
    description: str
    permissions: list[str]
    dependencies: list[str]
    error: str | None = None

    @classmethod
    def from_record(cls, record: PluginRecord) -> PluginInfo:
        manifest = record.manifest
        return cls(
            name=record.name,
            state=record.state.value,
            version=manifest.version if manifest else "",
            author=manifest.author if manifest else "",
            description=manifest.description if manifest else "",
            permissions=[p.value for p in manifest.permissions] if manifest else [],
            dependencies=list(manifest.dependencies) if manifest else [],
            error=record.error,
        )


class CommandInfo(BaseModel):
    plugin: str
    name: str
    description: str

    @classmethod
    def from_command(cls, command: Command) -> CommandInfo:
        return cls(plugin=command.plugin, name=command.name, description=command.description)


class SettingsPageInfo(BaseModel):
    plugin: str
    id: str
    title: str
    schema_: dict[str, Any] = Field(serialization_alias="schema")

    @classmethod
    def from_page(cls, page: SettingsPage) -> SettingsPageInfo:
        return cls(plugin=page.plugin, id=page.id, title=page.title, schema_=page.schema)


class UiPanelInfo(BaseModel):
    plugin: str
    id: str
    title: str
    location: str

    @classmethod
    def from_panel(cls, panel: UiPanel) -> UiPanelInfo:
        return cls(plugin=panel.plugin, id=panel.id, title=panel.title, location=panel.location)


class CommandExecuteRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class CommandResult(BaseModel):
    result: Any = None
