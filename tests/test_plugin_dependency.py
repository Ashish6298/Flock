"""Unit tests for PluginDependencyResolver."""

import pytest
from flock.plugins.exceptions import PluginDependencyError
from flock.plugins.models import PluginManifest
from flock.plugins.resolver import PluginDependencyResolver


def test_resolver_topological_sort() -> None:
    resolver = PluginDependencyResolver()

    m1 = PluginManifest(plugin_id="p1", name="p1", version="1", author="f", dependencies=[])
    m2 = PluginManifest(plugin_id="p2", name="p2", version="1", author="f", dependencies=["p1"])

    order = resolver.resolve_dependencies([m1, m2])
    assert order == ["p1", "p2"]


def test_resolver_detects_cycles() -> None:
    resolver = PluginDependencyResolver()

    m1 = PluginManifest(plugin_id="p1", name="p1", version="1", author="f", dependencies=["p2"])
    m2 = PluginManifest(plugin_id="p2", name="p2", version="1", author="f", dependencies=["p1"])

    with pytest.raises(PluginDependencyError):
        resolver.resolve_dependencies([m1, m2])
