"""Tool registry: name -> tool instance lookup.

Tools are registered as *instances* (they carry configuration such as sandbox
roots and injected backends), so the registry is built at startup by the
discovery helpers in :mod:`app.services.tools` rather than via import-time
decorators.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from app.services.tools.base import BaseTool, ToolNotFoundError


class ToolRegistry:
    """An ordered, name-indexed collection of tool instances."""

    def __init__(self, tools: Iterable[BaseTool[Any]] = ()) -> None:
        self._tools: dict[str, BaseTool[Any]] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: BaseTool[Any]) -> None:
        """Register a tool. Raises ``ValueError`` on duplicate names."""
        if not tool.name:
            raise ValueError(f"{type(tool).__name__} must define a non-empty 'name'")
        if tool.name in self._tools:
            raise ValueError(f"A tool named '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool if present (used when a plugin is disabled/unloaded)."""
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool[Any]:
        """Return the tool named ``name`` or raise :class:`ToolNotFoundError`."""
        try:
            return self._tools[name]
        except KeyError:
            raise ToolNotFoundError(f"Tool '{name}' is not registered") from None

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools)

    def specs(self) -> list[dict[str, Any]]:
        """Machine-readable specs for every registered tool."""
        return [tool.spec() for tool in self._tools.values()]

    def __iter__(self) -> Iterator[BaseTool[Any]]:
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)
