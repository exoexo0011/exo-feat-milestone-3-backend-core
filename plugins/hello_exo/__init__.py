"""hello_exo - the reference EXO plugin.

Demonstrates the plugin SDK: registering a tool and a command, subscribing to
chat events, contributing a settings page and UI panel, and using startup /
shutdown hooks. Everything is scoped by the permissions declared in plugin.json.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.plugins.sdk import (
    BaseTool,
    Event,
    EventName,
    PluginContext,
    ToolContext,
)


class GreetParams(BaseModel):
    name: str = Field(default="world", max_length=100, description="Who to greet")


class GreetTool(BaseTool[GreetParams]):
    name = "hello_greet"
    description = "Return a friendly greeting from the hello_exo plugin."
    params_model = GreetParams

    async def run(self, params: GreetParams, context: ToolContext) -> dict[str, Any]:
        return {"message": f"Hello, {params.name}! Greetings from the hello_exo plugin."}


def _greet_command(name: str = "world") -> dict[str, str]:
    return {"greeting": f"Hi {name}, this is a plugin command."}


def register(context: PluginContext) -> None:
    """Entry point invoked by the PluginManager during loading."""
    context.register_tool(GreetTool())
    context.register_command(
        "greet", _greet_command, description="Return a greeting for the given name."
    )
    context.register_settings_page("hello", "Hello Settings")
    context.register_ui_panel("hello-panel", "Hello", location="sidebar")

    def _on_response(event: Event) -> None:
        context.logger.info("hello_exo observed %s: %s", event.name, event.payload)

    context.subscribe(EventName.CHAT_RESPONSE_COMPLETED, _on_response)

    def _startup() -> None:
        context.logger.info("hello_exo enabled")

    def _shutdown() -> None:
        context.logger.info("hello_exo disabled")

    context.on_startup(_startup)
    context.on_shutdown(_shutdown)
