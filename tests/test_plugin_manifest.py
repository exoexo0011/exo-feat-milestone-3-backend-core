"""Tests for the plugin manifest model and version helpers."""

import pytest

from app.services.plugins.manifest import (
    PluginManifest,
    PluginPermission,
    parse_version,
    version_satisfies,
)


def test_parse_version_pads_to_triple() -> None:
    assert parse_version("1") == (1, 0, 0)
    assert parse_version("1.2") == (1, 2, 0)
    assert parse_version("1.2.3") == (1, 2, 3)


def test_version_satisfies() -> None:
    assert version_satisfies("0.8.0", "0.7.0")
    assert version_satisfies("0.8.0", "0.8.0")
    assert not version_satisfies("0.6.0", "0.7.0")


def test_manifest_permissions() -> None:
    manifest = PluginManifest(name="demo", version="1.0.0", permissions=["tool_access"])
    assert manifest.has_permission(PluginPermission.TOOL_ACCESS)
    assert not manifest.has_permission(PluginPermission.NETWORK)


@pytest.mark.parametrize("name", ["Bad Name", "UPPER", "has space", ""])
def test_invalid_names_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        PluginManifest(name=name)


def test_invalid_version_rejected() -> None:
    with pytest.raises(ValueError):
        PluginManifest(name="demo", version="not-a-version")


def test_compatibility_check() -> None:
    manifest = PluginManifest(name="demo", min_exo_version="0.9.0")
    assert not manifest.is_compatible_with("0.8.0")
    assert manifest.is_compatible_with("0.9.0")
    assert PluginManifest(name="demo").is_compatible_with("0.1.0")
