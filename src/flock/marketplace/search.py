"""Ecosystem integration search indices matching queries."""

from __future__ import annotations

import threading
from typing import Dict, List, Set
from flock.marketplace.models import PackageManifest


class MarketplaceSearchIndex:
    """Indexes manifest properties (keywords, descriptions) to support search queries."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # term -> set of package_ids
        self._index: Dict[str, Set[str]] = {}

    def index_package(self, manifest: PackageManifest) -> None:
        """Parse description and name to build lookup index keys."""
        with self._lock:
            # Simple word tokenizer
            tokens = (manifest.name + " " + manifest.description).lower().split()
            for token in tokens:
                clean = "".join(c for c in token if c.isalnum())
                if clean:
                    self._index.setdefault(clean, set()).add(manifest.package_id)

    def search(self, query: str) -> List[str]:
        """Search package IDs matching query terms."""
        with self._lock:
            clean_query = query.lower().strip()
            if not clean_query:
                return []
                
            results: Set[str] = set()
            terms = clean_query.split()
            
            # Simple OR search logic across terms
            for term in terms:
                matched = self._index.get(term, set())
                results.update(matched)
                
            return list(results)

    def clear_index(self) -> None:
        with self._lock:
            self._index.clear()
