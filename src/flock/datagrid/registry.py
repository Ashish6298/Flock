"""DataGrid Registry tracking collections and schema mappings."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.datagrid.models import BucketDefinition, CollectionDefinition


class DataGridRegistry:
    """Thread-safe index catalog mapping namespaces and buckets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # collection_name -> CollectionDefinition
        self._collections: Dict[str, CollectionDefinition] = {}
        
        # bucket_name -> BucketDefinition
        self._buckets: Dict[str, BucketDefinition] = {}

    def register_collection(self, collection: CollectionDefinition) -> None:
        """Register collection namespace."""
        with self._lock:
            self._collections[collection.name] = collection

    def get_collection(self, name: str) -> Optional[CollectionDefinition]:
        """Fetch matching collection namespace."""
        with self._lock:
            return self._collections.get(name)

    def register_bucket(self, bucket: BucketDefinition) -> None:
        """Register storage bucket definition."""
        with self._lock:
            self._buckets[bucket.bucket_name] = bucket

    def get_bucket(self, bucket_name: str) -> Optional[BucketDefinition]:
        """Fetch registered storage bucket."""
        with self._lock:
            return self._buckets.get(bucket_name)

    def list_collections(self) -> List[CollectionDefinition]:
        """List registered namespaces collections."""
        with self._lock:
            return list(self._collections.values())
