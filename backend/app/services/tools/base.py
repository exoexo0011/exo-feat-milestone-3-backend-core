"""Core abstractions for the tool framework.

A *tool* is a discrete, schema-validated capability the assistant can invoke
(arithmetic, filesystem access, launching apps, ...). Every tool declares:

* a unique ``name`` and human ``description``;
* a Pydantic parameter model (``params_model``) used to validate arguments;
* the set of :class:`Permission` categories it needs; and
* whether it ``requires_confirmation`` before running (destructive/irreversible).

Tools return a plain JSON-serialisable ``dict`` from :meth:`BaseTool.run` or
raise a :class:`ToolError`; the :class:`~app.services.tools.engine.ToolExecutionEngine`
wraps the outcome into a :class:`ToolResult` and records history. Keeping tools
free of HTTP/DB concerns makes them trivial to unit test.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ExoError

ParamsT = TypeVar("ParamsT", bound=BaseModel)


class Permission(StrEnum):
    """Capability categories a tool may require, gated by the permission policy."""

    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    SYSTEM = "system"
    PROCESS = "process"


class ToolStatus(StrEnum):
    """Terminal (or paused) state of a tool invocation."""

    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    CONFIRMATION_REQUIRED = "confirmation_required"


# --- error hierarchy --------------------------------------------------------


class ToolError(ExoError):
    """Base class for tool-related failures."""

    status_code = 400


class ToolNotFoundError(ToolError):
    """Requested tool is not registered."""

    status_code = 404


class ToolValidationError(ToolError):
    """Supplied arguments failed the tool's parameter schema."""

    status_code = 422


class ToolPermissionError(ToolError):
    """Tool needs a permission that the current policy denies."""

    status_code = 403


class ToolExecutionError(ToolError):
    """Tool ran but failed (I/O error, unsupported operation, ...)."""

    status_code = 500


# --- value types ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Runtime context passed to a tool for a single invocation."""

    confirmed: bool = False
    conversation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Outcome of a tool invocation as returned by the execution engine."""

    tool: str
    status: ToolStatus
    output: dict[str, Any] | None = None
    error: str | None = None
    action_id: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is ToolStatus.COMPLETED

    @property
    def needs_confirmation(self) -> bool:
        return self.status is ToolStatus.CONFIRMATION_REQUIRED


# --- tool interface ---------------------------------------------------------


class BaseTool(ABC, Generic[ParamsT]):
    """Abstract base every tool implements.

    Subclasses set the class attributes (``name``, ``description``,
    ``params_model``, ``permissions``, ``requires_confirmation``) and implement
    the async :meth:`run`.
    """

    name: ClassVar[str]
    description: ClassVar[str]
    requires_confirmation: ClassVar[bool] = False
    permissions: ClassVar[frozenset[Permission]] = frozenset()

    #: Pydantic model used to validate raw arguments. Set by each subclass.
    params_model: type[ParamsT]

    @abstractmethod
    async def run(self, params: ParamsT, context: ToolContext) -> dict[str, Any]:
        """Execute the tool with validated ``params`` and return JSON output."""

    def spec(self) -> dict[str, Any]:
        """Return a machine-readable description (used for AI tool-calling/UI)."""
        return {
            "name": self.name,
            "description": self.description,
            "requires_confirmation": self.requires_confirmation,
            "permissions": sorted(p.value for p in self.permissions),
            "parameters": self.params_model.model_json_schema(),
        }
