"""Unit and integration tests for Plugin CLI, Developer Experience & Workspace Tooling."""

from __future__ import annotations

import pytest

from flock.plugins.models import PluginManifest, PluginCLICommand
from flock.plugins.registry import PluginRegistry
from flock.plugins.cli import PluginCLI
from flock.plugins.exceptions import PluginWorkspaceError, PluginTemplateError


@pytest.fixture
def mock_manifest() -> PluginManifest:
    return PluginManifest(
        plugin_id="plugin-core",
        name="Core plugin framework",
        version="1.0.0",
        sdk_version="1.0.0",
        author="Tester",
        dependencies=[],
        capabilities=[],
    )


def test_initialize_workspace_happy_path() -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    workspace = cli.initialize_workspace(
        workspace_id="ws-dev",
        name="Flock Workspace Dev",
        root_path="D:/Flock/workspace",
    )

    assert workspace.workspace_id == "ws-dev"
    assert workspace.config.workspace_name == "Flock Workspace Dev"
    assert workspace.config.root_path == "D:/Flock/workspace"

    # Workspace details saved in registry
    saved_ws = registry.get_workspace("ws-dev")
    assert saved_ws is not None
    assert saved_ws.config.workspace_name == "Flock Workspace Dev"


def test_initialize_workspace_empty_path_raises() -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    with pytest.raises(PluginWorkspaceError):
        cli.initialize_workspace("ws-dev", "Workspace", "")


def test_scaffold_plugin_template() -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    # Setup template
    cli.generate_template("skeleton", "Plugin Skeleton", "Base scaffold outline template")

    # Scaffold new workspace plugin
    scaffold = cli.scaffold_workspace("new-plugin", "skeleton", "D:/Flock/workspace/new-plugin")

    assert scaffold.plugin_id == "new-plugin"
    assert scaffold.target_path == "D:/Flock/workspace/new-plugin"

    # Saved in registry
    scaffolds = registry.get_scaffolds("new-plugin")
    assert len(scaffolds) == 1
    assert scaffolds[0].target_path == "D:/Flock/workspace/new-plugin"


def test_scaffold_missing_template_raises() -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    with pytest.raises(PluginTemplateError):
        cli.scaffold_workspace("new-plugin", "unknown-temp", "path/to/target")


def test_workspace_summary_calculations(mock_manifest: PluginManifest) -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    cli.initialize_workspace("ws-dev", "Workspace", "root")
    
    registry.register_plugin(mock_manifest)
    
    summary = cli.workspace_summary("ws-dev")
    assert summary.plugins_registered_count == 1
    assert summary.active_plugins_count == 0


def test_execute_cli_commands() -> None:
    registry = PluginRegistry()
    cli = PluginCLI(registry)

    # 1. Test List Command (Empty)
    cmd_list = PluginCLICommand(command_name="list")
    res_list = cli.execute_cli_command(cmd_list)
    assert res_list.success is True
    assert "Plugins installed" in res_list.output

    # 2. Test Inspect Command
    # Inspect requires args
    cmd_inspect_no_args = PluginCLICommand(command_name="inspect")
    res_inspect_fail = cli.execute_cli_command(cmd_inspect_no_args)
    assert res_inspect_fail.success is False
    assert res_inspect_fail.error_message is not None

    # Inspect happy path (plugin not found outputs not found)
    cmd_inspect_args = PluginCLICommand(command_name="inspect", arguments=["unknown-plugin"])
    res_inspect_ok = cli.execute_cli_command(cmd_inspect_args)
    assert res_inspect_ok.success is True
    assert "not found" in res_inspect_ok.output

    # Verify history logs incremented
    stats = cli.inspect_cli_statistics()
    assert stats.total_executions == 3
    assert stats.successful_executions == 2
    assert stats.failed_executions == 1
