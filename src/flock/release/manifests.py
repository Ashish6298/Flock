"""Release Candidate (RC) verification manifests registry."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.release.exceptions import ReleaseError
from flock.release.models import ReleaseManifest


class ReleaseManifestRegistry:
    """Manages active compilation of Release Candidates metadata."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # version -> ReleaseManifest
        self._manifests: Dict[str, ReleaseManifest] = {}

    def register_release_candidate(self, manifest: ReleaseManifest) -> None:
        """Register a release candidate document."""
        with self._lock:
            self._manifests[manifest.version] = manifest

    def get_release_candidate(self, version: str) -> ReleaseManifest:
        with self._lock:
            if version not in self._manifests:
                raise ReleaseError(f"Release candidate version '{version}' not found.")
            return self._manifests[version]

    def list_release_candidates(self) -> List[ReleaseManifest]:
        with self._lock:
            return list(self._manifests.values())
