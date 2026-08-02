"""Plugin Discovery Engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Set
import structlog
from flock.plugins.models import PluginManifest
from flock.plugins.validation import PluginValidator

logger = structlog.get_logger()


class PluginDiscovery:
    """Discovers plugins in directories and validates their manifests."""

    def __init__(self, search_paths: List[str] | None = None) -> None:
        self.search_paths = search_paths or []

    def discover_plugins(self) -> List[PluginManifest]:
        """Scans all configured search paths for manifest.json files."""
        discovered: List[PluginManifest] = []
        seen_ids: Set[str] = set()

        for path_str in self.search_paths:
            path = Path(path_str)
            if not path.exists() or not path.is_dir():
                continue

            # Look for subdirectories containing manifest.json
            for sub_dir in path.iterdir():
                if not sub_dir.is_dir():
                    continue

                manifest_path = sub_dir / "manifest.json"
                if not manifest_path.exists():
                    continue

                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    manifest = PluginManifest(**data)
                    PluginValidator.validate_manifest(manifest)

                    if manifest.plugin_id in seen_ids:
                        logger.warning(
                            "Duplicate plugin ID discovered, skipping",
                            plugin_id=manifest.plugin_id,
                            path=str(manifest_path),
                        )
                        continue

                    seen_ids.add(manifest.plugin_id)
                    discovered.append(manifest)

                except Exception as exc:
                    logger.error(
                        "Failed to parse plugin manifest",
                        path=str(manifest_path),
                        error=str(exc),
                    )

        return discovered
