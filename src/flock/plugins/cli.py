"""Plugin CLI Command Executor and Workspace Scaffolding Tooling.

Exposes a unified PluginCLI orchestrating workspace init, scaffolding targets,
manifest validation, certification pipelines, diagnostics views, and packages.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

import structlog

from flock.plugins.exceptions import (
    PluginCommandError,
    PluginTemplateError,
    PluginWorkspaceError,
)
from flock.plugins.models import (
    PluginCLICommand,
    PluginCLIResult,
    PluginCLIStatistics,
    PluginCommandHistory,
    PluginManifest,
    PluginScaffold,
    PluginTemplate,
    PluginWorkspace,
    PluginWorkspaceConfiguration,
    PluginWorkspaceSummary,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginCLI:
    """Consolidated CLI frontend executing workspace initializations and command delegations."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def initialize_workspace(self, workspace_id: str, name: str, root_path: str) -> PluginWorkspace:
        """Saves a workspace configuration and initializes the metadata files mapping."""
        # Validate workspace target paths
        if not root_path or len(root_path) == 0:
            raise PluginWorkspaceError("Workspace root path cannot be empty.")

        config = PluginWorkspaceConfiguration(
            workspace_name=name,
            root_path=root_path,
        )
        workspace = PluginWorkspace(
            workspace_id=workspace_id,
            config=config,
            created_at=datetime.now(timezone.utc),
        )
        self._registry.save_workspace(workspace)
        return workspace

    def list_plugins(self) -> List[str]:
        """Lists active plugin names registered in catalogs."""
        return [manifest.plugin_id for manifest in self._registry.list_plugins()]

    def inspect_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """Gets active plugin details matching plugin_id."""
        return self._registry.get_plugin(plugin_id)

    def validate_plugin(self, manifest: PluginManifest) -> bool:
        """Audits structural integrity parameters and manifest mappings."""
        # Reuse Phase 1 validations checklist basics
        if not manifest.plugin_id or len(manifest.plugin_id) == 0:
            return False
        if not manifest.version or len(manifest.version) == 0:
            return False
        return True

    def generate_template(self, template_id: str, name: str, description: str) -> PluginTemplate:
        """Registers a named plugin template framework."""
        files = {
            "manifest.json": '{\n  "plugin_id": "skeleton-plugin",\n  "name": "Skeleton plugin",\n  "version": "1.0.0",\n  "sdk_version": "1.0.0"\n}',
            "__init__.py": '"""Skeleton plugin main module."""\n',
        }
        template = PluginTemplate(
            template_id=template_id,
            name=name,
            description=description,
            files=files,
        )
        self._registry.save_template(template)
        return template

    def scaffold_workspace(self, plugin_id: str, template_id: str, target_dir: str) -> PluginScaffold:
        """Saves generated scaffold directory details logs."""
        template = self._registry.get_template(template_id)
        if template is None:
            raise PluginTemplateError(f"Cannot generate scaffold: template '{template_id}' not found.")

        scaffold = PluginScaffold(
            scaffold_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            target_path=target_dir,
            generated_at=datetime.now(timezone.utc),
        )
        self._registry.save_scaffold(scaffold)
        return scaffold

    def workspace_summary(self, workspace_id: str) -> PluginWorkspaceSummary:
        """Exposes workspace summary details."""
        workspace = self._registry.get_workspace(workspace_id)
        if workspace is None:
            raise PluginWorkspaceError(f"Workspace '{workspace_id}' not found.")

        plugins = self._registry.list_plugins()
        return PluginWorkspaceSummary(
            workspace_id=workspace_id,
            plugins_registered_count=len(plugins),
            active_plugins_count=len([p for p in plugins if self._registry.is_activated(p.plugin_id)]),
        )

    def execute_cli_command(self, cmd: PluginCLICommand) -> PluginCLIResult:
        """Audits command execution parameter mappings and appends history records."""
        start_time = datetime.now(timezone.utc)
        output = ""
        success = True
        err_msg = None

        try:
            name = cmd.command_name.lower()
            if name == "list":
                plugins = self.list_plugins()
                output = f"Plugins installed: {', '.join(plugins)}"
            elif name == "inspect":
                if not cmd.arguments:
                    raise PluginCommandError("Inspect command requires a plugin_id argument.")
                p_id = cmd.arguments[0]
                manifest = self.inspect_plugin(p_id)
                if manifest is None:
                    output = f"Plugin '{p_id}' not found."
                else:
                    output = f"Plugin '{p_id}' version={manifest.version}"
            else:
                raise PluginCommandError(f"Unrecognized CLI command: '{cmd.command_name}'.")
        except Exception as exc:
            success = False
            output = ""
            err_msg = str(exc)

        res = PluginCLIResult(
            success=success,
            output=output,
            error_message=err_msg,
        )

        history_record = PluginCommandHistory(
            history_id=str(uuid.uuid4()),
            command=cmd,
            result=res,
            executed_at=start_time,
        )
        self._registry.record_command_history(history_record)
        return res

    def inspect_cli_statistics(self) -> PluginCLIStatistics:
        """Retrieves and calculates statistics from execution history logs."""
        history = self._registry.get_command_history()
        total = len(history)
        succeeded = len([h for h in history if h.result.success])
        failed = total - succeeded

        return PluginCLIStatistics(
            total_executions=total,
            successful_executions=succeeded,
            failed_executions=failed,
        )
