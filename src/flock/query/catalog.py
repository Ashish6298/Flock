"""Query Catalog tracking table schemas and collections."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.query.exceptions import CatalogNotFoundError
from flock.query.models import CatalogEntry


class QueryCatalog:
    """Thread-safe metadata directory mapping table structures."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # table_name -> CatalogEntry
        self._entries: Dict[str, CatalogEntry] = {}

    def register_table(self, entry: CatalogEntry) -> None:
        """Register table schema definition."""
        with self._lock:
            self._entries[entry.name] = entry

    def get_table(self, name: str) -> Optional[CatalogEntry]:
        """Fetch table schema.

        Raises:
            CatalogNotFoundError: If table name is missing.
        """
        with self._lock:
            entry = self._entries.get(name)
            if not entry:
                raise CatalogNotFoundError(f"Table '{name}' not found in QueryCatalog registry.")
            return entry

    def list_tables(self) -> List[CatalogEntry]:
        """List registered table catalog profiles."""
        with self._lock:
            return list(self._entries.values())
