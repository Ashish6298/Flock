"""Execution Recorder tracking invocation logs and metadata."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.functions.models import InvocationResult


class ExecutionRecorder:
    """Thread-safe storage indexing invocation outcomes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # invocation_id -> InvocationResult
        self._records: Dict[str, InvocationResult] = {}

    def record_result(self, result: InvocationResult) -> None:
        """Register invocation outcome snapshot."""
        with self._lock:
            self._records[result.invocation_id] = result

    def get_result(self, invocation_id: str) -> Optional[InvocationResult]:
        """Fetch historical result match."""
        with self._lock:
            return self._records.get(invocation_id)
