"""REST endpoints for inspecting and controlling plugins.

Security note: enabling/disabling plugins and running plugin commands are
privileged local operations. Like the rest of the backend they are
unauthenticated (local-first); add authentication before remote exposure.
"""

from fastapi import APIRouter

from app.api.deps import PluginManagerDep
from app.schemas.plugins import (
    CommandExecuteRequest,
    CommandInfo,
    CommandResult,
    PluginInfo,
    SettingsPageInfo,
    UiPanelInfo,
)

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginInfo])
async def list_plugins(manager: PluginManagerDep) -> list[PluginInfo]:
    """List all discovered plugins and their state."""
    return [PluginInfo.from_record(record) for record in manager.registry.all()]


@router.get("/commands", response_model=list[CommandInfo])
async def list_commands(manager: PluginManagerDep) -> list[CommandInfo]:
    """List commands contributed by enabled plugins."""
    return [CommandInfo.from_command(command) for command in manager.commands()]


@router.get("/settings-pages", response_model=list[SettingsPageInfo])
async def list_settings_pages(manager: PluginManagerDep) -> list[SettingsPageInfo]:
    return [SettingsPageInfo.from_page(page) for page in manager.settings_pages()]


@router.get("/ui-panels", response_model=list[UiPanelInfo])
async def list_ui_panels(manager: PluginManagerDep) -> list[UiPanelInfo]:
    return [UiPanelInfo.from_panel(panel) for panel in manager.ui_panels()]


@router.post("/commands/{plugin}/{name}", response_model=CommandResult)
async def execute_command(
    plugin: str, name: str, payload: CommandExecuteRequest, manager: PluginManagerDep
) -> CommandResult:
    """Invoke a plugin command with keyword arguments."""
    result = await manager.execute_command(plugin, name, payload.arguments)
    return CommandResult(result=result)


@router.get("/{name}", response_model=PluginInfo)
async def get_plugin(name: str, manager: PluginManagerDep) -> PluginInfo:
    return PluginInfo.from_record(manager.registry.get(name))


@router.post("/{name}/enable", response_model=PluginInfo)
async def enable_plugin(name: str, manager: PluginManagerDep) -> PluginInfo:
    return PluginInfo.from_record(await manager.enable(name))


@router.post("/{name}/disable", response_model=PluginInfo)
async def disable_plugin(name: str, manager: PluginManagerDep) -> PluginInfo:
    return PluginInfo.from_record(await manager.disable(name))


@router.post("/{name}/reload", response_model=PluginInfo)
async def reload_plugin(name: str, manager: PluginManagerDep) -> PluginInfo:
    return PluginInfo.from_record(await manager.reload(name))
