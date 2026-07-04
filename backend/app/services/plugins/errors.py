"""Plugin subsystem error hierarchy (mapped to HTTP by the domain handler)."""

from app.core.exceptions import ExoError


class PluginError(ExoError):
    """Base class for plugin failures."""

    status_code = 400


class PluginManifestError(PluginError):
    """A plugin.json manifest is missing or invalid."""

    status_code = 422


class PluginNotFoundError(PluginError):
    """Requested plugin is not registered."""

    status_code = 404


class PluginPermissionError(PluginError):
    """A plugin attempted an operation outside its granted permissions."""

    status_code = 403


class PluginVersionError(PluginError):
    """A plugin declares an EXO version requirement that is not satisfied."""

    status_code = 409


class PluginDependencyError(PluginError):
    """A plugin's declared dependencies are missing or form a cycle."""

    status_code = 409


class PluginLoadError(PluginError):
    """A plugin failed to import or register."""

    status_code = 500
