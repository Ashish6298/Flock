"""Data models representing execution results, failures, and metadata envelopes."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class FailureResult:
    """Encapsulates execution error metadata details."""
    exception_type: str
    exception_message: str
    traceback: str
    retryable: bool = False
    failure_stage: str = "EXECUTION"
    diagnostic_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ResultMetadata:
    """Contains serialization and verification metadata metrics."""
    protocol_version: int = 1
    serializer_name: str = "json"
    checksum_algo: str = "sha256"
    payload_size: int = 0
    compression_flag: bool = False
    correlation_id: Optional[str] = None

@dataclass(frozen=True)
class ExecutionResult:
    """Immutable representation of a task's returned value or failure profile."""
    task_id: str
    node_id: str
    completed_timestamp: float
    duration_ms: float
    serialized_value: bytes
    checksum: str
    success: bool = True
    failure: Optional[FailureResult] = None
    metadata: ResultMetadata = field(default_factory=ResultMetadata)
