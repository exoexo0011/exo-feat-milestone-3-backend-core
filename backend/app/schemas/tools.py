"""Schemas for the tools REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.tools.base import ToolResult, ToolStatus


class ToolSpec(BaseModel):
    """Machine-readable description of a registered tool."""

    name: str
    description: str
    requires_confirmation: bool
    permissions: list[str]
    parameters: dict[str, Any]


class ToolExecuteRequest(BaseModel):
    """Request body to execute a tool."""

    arguments: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False
    conversation_id: str | None = None


class ToolResultResponse(BaseModel):
    """Uniform result of a tool invocation."""

    tool: str
    status: ToolStatus
    output: dict[str, Any] | None = None
    error: str | None = None
    action_id: str | None = None

    @classmethod
    def from_result(cls, result: ToolResult) -> ToolResultResponse:
        return cls(
            tool=result.tool,
            status=result.status,
            output=result.output,
            error=result.error,
            action_id=result.action_id,
        )
