"""Fleet inventory catalog search indexes."""

from __future__ import annotations

import threading
from typing import Dict, List, Set


class FleetInventoryCatalog:
    """Maintains indexed records of cluster resources and labels for fleet-wide search queries."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # label_key -> val -> set of cluster_ids
        self._labels_index: Dict[str, Dict[str, Set[str]]] = {}

    def index_cluster_labels(self, cluster_id: str, labels: Dict[str, str]) -> None:
        """Register and index cluster labels for search routing queries."""
        with self._lock:
            for k, v in labels.items():
                vals = self._labels_index.setdefault(k, {})
                clusters = vals.setdefault(v, set())
                clusters.add(cluster_id)

    def search_by_label(self, key: str, value: str) -> List[str]:
        """Search cluster IDs matching the target label key/value pair."""
        with self._lock:
            return list(self._labels_index.get(key, {}).get(value, set()))

    def clear_indices(self) -> None:
        """Clear all search indices."""
        with self._lock:
            self._labels_index.clear()
