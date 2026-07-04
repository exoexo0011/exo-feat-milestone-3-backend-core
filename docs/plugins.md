# Plugin Framework

Milestone 8 adds a production-ready plugin architecture. Plugins extend EXO with
new tools, commands, API routes, UI contributions and event handlers, governed
by a declared permission set and loaded with strong failure isolation.

## Anatomy of a plugin

A plugin is a directory under the plugins folder (`EXO_PLUGINS_DIR`, default
`../plugins`) containing a manifest and a Python package:

```
plugins/
└── my_plugin/
    ├── plugin.json     # manifest
    └── __init__.py     # exposes register(context)
```

### plugin.json

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "You",
  "description": "What it does.",
  "permissions": ["tool_access", "notifications"],
  "dependencies": [],
  "min_exo_version": "0.8.0",
  "entry_point": "register",
  "enabled_by_default": true
}
```

- `name` must be lowercase (`^[a-z0-9][a-z0-9_-]*$`) and match the directory name.
- `permissions` — see the table below.
- `dependencies` — names of other plugins that must load first.
- `min_exo_version` — the plugin is skipped (marked `error`) on older EXO.
- `entry_point` — the callable in `__init__.py` (default `register`).

### Entry point

```python
from app.services.plugins.sdk import BaseTool, PluginContext, ToolContext, EventName, Event

def register(context: PluginContext) -> None:
    context.register_tool(MyTool())
    context.register_command("hello", lambda name="world": {"msg": f"hi {name}"})
    context.subscribe(EventName.CHAT_RESPONSE_COMPLETED, lambda e: context.logger.info("chat done"))
    context.on_startup(lambda: context.logger.info("started"))
    context.on_shutdown(lambda: context.logger.info("stopped"))
```

`register` is **pure recording**: it declares contributions but performs no side
effects. The `PluginManager` *applies* them on enable and *reverts* them on
disable, so enabling/disabling is symmetric and a `register` that raises midway
leaves no partial state.

## Permissions

| Permission | Grants |
|---|---|
| `filesystem_read` | tools that read files |
| `filesystem_write` | tools that write files |
| `clipboard` | tools that use the clipboard |
| `network` | tools/handlers that make network calls |
| `notifications` | `context.notify(...)` |
| `tool_access` | `context.register_tool(...)` |
| `settings_access` | `context.get_setting` / `set_setting` |

A plugin may only register a tool whose capabilities map to permissions it holds
(e.g. a tool declaring `FILESYSTEM_WRITE` requires the plugin to hold
`filesystem_write`). Tools requiring `SYSTEM`/`PROCESS` cannot be provided by
plugins.

## The PluginContext API

- `register_tool(tool)` — contribute a `BaseTool` (needs `tool_access`).
- `register_command(name, handler, *, description="")` — a callable invoked via
  the API; may be sync or async and returns JSON-serialisable data.
- `register_router(router)` / `register_websocket(path, handler)` — mounted
  under `/api/plugins/<name>`.
- `register_settings_page(id, title, schema=None)` / `register_ui_panel(id,
  title, location="sidebar")` — UI descriptors exposed to the frontend.
- `on_startup(hook)` / `on_shutdown(hook)` — run on enable / disable.
- `subscribe(event_name, handler)` — subscribe to the event bus.
- `notify(title, body)` — publish a notification (needs `notifications`).
- `get_setting(key, default)` / `set_setting(key, value)` — per-plugin settings
  (needs `settings_access`).
- `logger` — a namespaced logger (`exo.plugin.<name>`).

## Event system

The `EventBus` is pub/sub with per-handler error isolation. Built-in events
(`app.services.eventbus.EventName`):

- `system.startup`, `system.shutdown`
- `plugin.loaded`, `plugin.enabled`, `plugin.disabled`, `plugin.error`
- `chat.message_created`, `chat.response_completed`
- `tool.executed`

Subscribe to `EventName.WILDCARD` to receive every event. Handlers may be sync
or async; exceptions are logged and never propagate.

## Lifecycle & isolation

States: `discovered → enabled | disabled | error`. The manager:

1. **discovers** plugin directories and validates manifests;
2. orders them by dependencies (missing/circular deps → `error`);
3. checks version compatibility;
4. imports each package under a unique module name (`exo_plugins.<name>`);
5. calls `register(context)` and, if `enabled_by_default`, activates it.

Every step is wrapped: a plugin that fails to import, register, or run a hook is
marked `error` with a message and **never crashes the application** or affects
other plugins. Enable/disable/reload are available at runtime via the REST API.

## REST API

Under `/api/plugins`:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/plugins` | List plugins and state |
| `GET` | `/plugins/{name}` | One plugin |
| `POST` | `/plugins/{name}/enable` \| `/disable` \| `/reload` | Lifecycle control |
| `GET` | `/plugins/commands` | Commands from enabled plugins |
| `POST` | `/plugins/commands/{plugin}/{name}` | Run a command (`{arguments}`) |
| `GET` | `/plugins/settings-pages` \| `/ui-panels` | UI contributions |

## Security model & limitations

Permissions are validated and enforced at the `PluginContext` boundary, tool
capabilities are checked against grants, and destructive tools still use the
tool confirmation flow. **However, plugins run in-process**: Python provides no
true sandbox, so a determined plugin can bypass permission checks by importing
modules directly. Treat plugins like any dependency - only install trusted code.
Full process/OS isolation (subprocess or WASM) is future work. Plugin-mounted
API routes persist for the process lifetime (disable stops tools/commands/
events/hooks but not already-mounted routes).

## Example

See `plugins/hello_exo/` for a complete reference plugin (a tool, a command, an
event subscriber, a settings page, a UI panel, and startup/shutdown hooks).

## Testing plugins

Construct a `PluginManager` against a temporary directory:

```python
manager = PluginManager(tmp_dir, tool_registry=ToolRegistry(),
                        event_bus=EventBus(), exo_version="0.8.0")
await manager.discover_and_load()
```

See `tests/test_plugins.py` and `tests/test_plugins_api.py`.
