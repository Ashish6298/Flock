"""Global configuration schemas validation and updates distribution."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import GlobalConfigurationError


class ConfigurationManager:
    """Manages versioned configuration overrides distributed to fleet clusters."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # config_key -> config_value
        self._configs: Dict[str, str] = {}
        self._versions: Dict[str, int] = {}

    def set_config(self, key: str, value: str) -> None:
        """Set a configuration parameter override, incrementing its version identifier."""
        with self._lock:
            if not key:
                raise GlobalConfigurationError("Configuration key cannot be empty.")
            self._configs[key] = value
            version = self._versions.get(key, 0) + 1
            self._versions[key] = version

    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value."""
        with self._lock:
            return self._configs.get(key)

    def get_config_version(self, key: str) -> int:
        """Get config parameter version counter."""
        with self._lock:
            return self._versions.get(key, 0)

    def list_configs(self) -> Dict[str, str]:
        """List all active configuration overrides."""
        with self._lock:
            return dict(self._configs)
