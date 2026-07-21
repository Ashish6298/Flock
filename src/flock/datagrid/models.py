"""DataGrid Subsystem Models."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    """Represents a temporary in-memory cached entry."""
    key: str
    value: Any
    expires_at: Optional[float] = None

    model_config = {
        "frozen": True
    }


class KeyValueRecord(BaseModel):
    """Represents a versioned persistent key-value record."""
    key: str
    value: Any
    version: int = 1

    model_config = {
        "frozen": True
    }


class ObjectRecord(BaseModel):
    """Represents a binary object storage payload record."""
    object_key: str
    payload: bytes
    checksum: str

    model_config = {
        "frozen": True
    }


class BucketDefinition(BaseModel):
    """Represents a collection bucket partitioning scheme."""
    bucket_name: str
    quota_limit: int = 10485760  # Default 10MB limit

    model_config = {
        "frozen": True
    }


class LockLease(BaseModel):
    """Represents an active distributed mutual exclusion lease."""
    lock_key: str
    lease_id: str
    expires_at: float

    model_config = {
        "frozen": True
    }


class CollectionDefinition(BaseModel):
    """Represents logical grouping schema namespaces."""
    name: str

    model_config = {
        "frozen": True
    }


class IndexDefinition(BaseModel):
    """Represents secondary index definitions fields."""
    index_name: str
    target_field: str

    model_config = {
        "frozen": True
    }
