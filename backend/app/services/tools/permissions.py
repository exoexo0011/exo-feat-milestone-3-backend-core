"""Permission policy.

The policy is the hard allow/deny gate for tool capability categories. It is
distinct from *confirmation*: confirmation asks the user before a permitted but
sensitive action, whereas a denied permission blocks the tool outright
regardless of confirmation. Deny lists come from application settings, so an
operator can, for example, disable all filesystem writes centrally.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.config import Settings
from app.services.tools.base import BaseTool, Permission, ToolPermissionError


class PermissionPolicy:
    """Decides whether a tool's required permissions are allowed."""

    def __init__(self, denied: Iterable[Permission] = ()) -> None:
        self._denied: frozenset[Permission] = frozenset(denied)

    @property
    def denied(self) -> frozenset[Permission]:
        return self._denied

    def is_allowed(self, permission: Permission) -> bool:
        return permission not in self._denied

    def check(self, tool: BaseTool[Any]) -> None:
        """Raise :class:`ToolPermissionError` if any required permission is denied."""
        blocked = sorted(p.value for p in tool.permissions if p in self._denied)
        if blocked:
            raise ToolPermissionError(
                f"Tool '{tool.name}' requires denied permission(s): {', '.join(blocked)}"
            )

    @classmethod
    def from_settings(cls, settings: Settings) -> PermissionPolicy:
        """Build a policy from ``settings.tool_denied_permissions``.

        Unknown permission names raise ``ValueError`` early so a typo in
        configuration fails loudly at startup rather than silently allowing.
        """
        denied: list[Permission] = []
        for name in settings.tool_denied_permissions:
            try:
                denied.append(Permission(name))
            except ValueError as exc:
                valid = ", ".join(p.value for p in Permission)
                raise ValueError(
                    f"Unknown permission '{name}' in tool_denied_permissions. Valid: {valid}"
                ) from exc
        return cls(denied)
