"""Low-level plugin loading: manifest parsing and safe module import.

A plugin is a directory containing ``plugin.json`` and a Python package
(``__init__.py``) exposing a ``register(context)`` callable. Modules are
imported by explicit file location under a unique module name so plugins are
isolated from each other and from the application's import namespace.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast

from app.services.plugins.context import PluginContext
from app.services.plugins.errors import PluginLoadError, PluginManifestError
from app.services.plugins.manifest import PluginManifest

MANIFEST_FILENAME = "plugin.json"
RegisterFn = Callable[[PluginContext], None]


def _module_name(plugin_name: str) -> str:
    return f"exo_plugins.{plugin_name}"


def discover_plugin_dirs(plugins_dir: Path) -> list[Path]:
    """Return sorted plugin directories (those containing a manifest)."""
    if not plugins_dir.is_dir():
        return []
    return sorted(
        entry
        for entry in plugins_dir.iterdir()
        if entry.is_dir() and (entry / MANIFEST_FILENAME).is_file()
    )


def load_manifest(plugin_dir: Path) -> PluginManifest:
    """Read and validate ``plugin.json`` from ``plugin_dir``."""
    manifest_path = plugin_dir / MANIFEST_FILENAME
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PluginManifestError(f"Cannot read manifest at {manifest_path}: {exc}") from exc
    try:
        return PluginManifest.model_validate(raw)
    except ValueError as exc:
        raise PluginManifestError(f"Invalid manifest at {manifest_path}: {exc}") from exc


def import_plugin_module(plugin_name: str, plugin_dir: Path) -> ModuleType:
    """Import the plugin package from its directory under a unique module name."""
    init_file = plugin_dir / "__init__.py"
    if not init_file.is_file():
        raise PluginLoadError(f"Plugin '{plugin_name}' has no __init__.py")

    module_name = _module_name(plugin_name)
    # Replace any stale module of the same name (supports reload).
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(
        module_name, init_file, submodule_search_locations=[str(plugin_dir)]
    )
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"Could not create import spec for plugin '{plugin_name}'")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - surface any import-time failure uniformly
        sys.modules.pop(module_name, None)
        raise PluginLoadError(f"Plugin '{plugin_name}' failed to import: {exc}") from exc
    return module


def get_register_callable(module: ModuleType, entry_point: str) -> RegisterFn:
    """Resolve the plugin's ``register`` callable from ``entry_point``.

    ``entry_point`` is an attribute name on the plugin's top-level module.
    """
    target = getattr(module, entry_point, None)
    if not callable(target):
        raise PluginLoadError(f"Entry point '{entry_point}' is not a callable in the plugin module")
    return cast(RegisterFn, target)


def unload_module(plugin_name: str) -> None:
    """Drop the plugin's module (and submodules) from ``sys.modules``."""
    prefix = _module_name(plugin_name)
    for name in [key for key in sys.modules if key == prefix or key.startswith(f"{prefix}.")]:
        del sys.modules[name]
