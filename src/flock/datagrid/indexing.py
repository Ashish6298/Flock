"""Secondary Indexing Engine."""

from __future__ import annotations

import threading
from typing import Dict, List, Set


class IndexEngine:
    """Manages secondary index registries without nondeterministic paths."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # index_name -> {field_value -> {record_keys}}
        self._indexes: Dict[str, Dict[str, Set[str]]] = {}

    def add_index_value(self, index_name: str, value: str, record_key: str) -> None:
        """Register index reference link."""
        with self._lock:
            if index_name not in self._indexes:
                self._indexes[index_name] = {}
            
            val_map = self._indexes[index_name]
            if value not in val_map:
                val_map[value] = set()
            
            val_map[value].add(record_key)

    def lookup_index(self, index_name: str, value: str) -> List[str]:
        """Fetch references matching target values."""
        with self._lock:
            val_map = self._indexes.get(index_name)
            if not val_map:
                return []
            
            keys_set = val_map.get(value)
            if not keys_set:
                return []
            
            return sorted(list(keys_set))
