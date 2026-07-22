"""Distributed checkpoint synchronization and integrity validations."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.recovery.exceptions import CheckpointError
from flock.recovery.models import CheckpointDescriptor
from flock.security.encryption import CryptographyEngine


class CheckpointManager:
    """Creates and coordinates distributed metadata checkpoints."""

    def __init__(self, crypto: CryptographyEngine) -> None:
        self._crypto = crypto
        self._lock = threading.RLock()
        # checkpoint_id -> CheckpointDescriptor
        self._checkpoints: Dict[str, CheckpointDescriptor] = {}
        self._seq_counter = 0

    def create_checkpoint(
        self,
        coordinator_node: str,
        snapshot_id: str,
    ) -> CheckpointDescriptor:
        """Create a new distributed checkpoint and sign its integrity metadata."""
        with self._lock:
            self._seq_counter += 1
            checkpoint_id = f"chk-{self._seq_counter}"
            now = time.time()
            
            # Sign the checkpoint properties to guarantee integrity
            payload = f"{checkpoint_id}:{self._seq_counter}:{snapshot_id}:{coordinator_node}".encode("utf-8")
            signature = self._crypto.sign_data(payload)
            
            desc = CheckpointDescriptor(
                checkpoint_id=checkpoint_id,
                sequence_number=self._seq_counter,
                timestamp=now,
                coordinator_node_id=coordinator_node,
                snapshot_id=snapshot_id,
                integrity_signature=signature,
            )
            self._checkpoints[checkpoint_id] = desc
            return desc

    def validate_checkpoint(self, checkpoint: CheckpointDescriptor) -> bool:
        """Validate integrity signature and parameters of a checkpoint descriptor.
        
        Raises:
            CheckpointError: If validation signature is corrupted.
        """
        payload = f"{checkpoint.checkpoint_id}:{checkpoint.sequence_number}:{checkpoint.snapshot_id}:{checkpoint.coordinator_node_id}".encode("utf-8")
        try:
            self._crypto.verify_signature(payload, checkpoint.integrity_signature)
            return True
        except Exception as exc:
            raise CheckpointError(f"Checkpoint integrity verification failed: {exc}") from exc

    def get_checkpoint(self, checkpoint_id: str) -> CheckpointDescriptor:
        """Retrieve checkpoint details."""
        with self._lock:
            if checkpoint_id not in self._checkpoints:
                raise CheckpointError(f"Checkpoint '{checkpoint_id}' not found.")
            return self._checkpoints[checkpoint_id]

    def list_checkpoints(self) -> List[CheckpointDescriptor]:
        """List all synchronized checkpoints."""
        with self._lock:
            return list(self._checkpoints.values())
