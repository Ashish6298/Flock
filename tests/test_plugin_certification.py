"""Unit and integration tests for Plugin Testing, Certification & QA Framework."""

from __future__ import annotations

import time
import pytest

from flock.plugins.models import PluginManifest, PluginPermission, PermissionScope
from flock.plugins.registry import PluginRegistry
from flock.plugins.certification import PluginCertificationEngine
from flock.plugins.exceptions import PluginCertificationFailure


@pytest.fixture
def mock_plugin_manifest() -> PluginManifest:
    return PluginManifest(
        plugin_id="plugin-db",
        name="SQL database plugin",
        version="1.0.0",
        sdk_version="1.0.0",
        author="Tester",
        dependencies=[],
        capabilities=[],
        entry_point="flock.plugins.db:DBPlugin",
    )


def test_conformance_check_pass(mock_plugin_manifest: PluginManifest) -> None:
    registry = PluginRegistry()
    engine = PluginCertificationEngine(registry, sdk_version="1.0.0")

    registry.register_plugin(mock_plugin_manifest)
    
    # Declare one permission grant to pass the security rules check
    registry.grant_permission(
        PluginPermission(
            permission_id="p-1",
            plugin_id="plugin-db",
            scope=PermissionScope.READ,
            resource="db",
        )
    )

    report = engine.run_certification("plugin-db")

    assert report.plugin_id == "plugin-db"
    assert report.status.value == "CERTIFIED"
    assert report.quality_score.overall_score == 100.0
    assert len(report.compliance.failed_rules) == 0


def test_conformance_fails_for_missing_entrypoint(mock_plugin_manifest: PluginManifest) -> None:
    registry = PluginRegistry()
    engine = PluginCertificationEngine(registry, sdk_version="1.0.0")

    # Entrypoint set to None should trigger compliance failures
    malformed_manifest = PluginManifest(
        plugin_id="plugin-db",
        name="SQL database plugin",
        version="1.0.0",
        sdk_version="1.0.0",
        author="Tester",
        dependencies=[],
        capabilities=[],
        entry_point=None,
    )
    registry.register_plugin(malformed_manifest)

    report = engine.run_certification("plugin-db")
    assert report.status.value == "CONDITIONALLY_CERTIFIED"
    assert "EntryPointDefined" in report.compliance.failed_rules


def test_conformance_fails_for_sdk_mismatch(mock_plugin_manifest: PluginManifest) -> None:
    registry = PluginRegistry()
    engine = PluginCertificationEngine(registry, sdk_version="2.0.0")

    registry.register_plugin(mock_plugin_manifest)

    report = engine.run_certification("plugin-db")
    assert report.status.value == "FAILED"
    assert report.quality_score.overall_score < 70.0


def test_compare_certifications_delta(mock_plugin_manifest: PluginManifest) -> None:
    registry = PluginRegistry()
    engine = PluginCertificationEngine(registry, sdk_version="1.0.0")
    registry.register_plugin(mock_plugin_manifest)

    # Initial report (passes except missing entry_point if malformed, but here passes completely)
    report_a = engine.run_certification("plugin-db")

    # Register updated plugin with SDK version mismatch
    registry.unregister_plugin("plugin-db")
    malformed_manifest = PluginManifest(
        plugin_id="plugin-db",
        name="SQL database plugin",
        version="1.0.0",
        sdk_version="2.0.0",
        author="Tester",
    )
    registry.register_plugin(malformed_manifest)

    report_b = engine.run_certification("plugin-db")

    delta = engine.compare_certifications(report_a, report_b)
    assert delta["score_difference"] < 0.0
    assert delta["status_changed"] is True
