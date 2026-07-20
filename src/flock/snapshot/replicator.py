"""Incremental snapshot replicator."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from typing import Any, Dict, List, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.protocol.packet import MessageType
from flock.snapshot.exceptions import (
    SnapshotChunkValidationError,
    SnapshotTransferError,
)
from flock.snapshot.models import (
    SnapshotChunk,
    SnapshotManifest,
    SnapshotMetadata,
    SnapshotTransferSession,
)
from flock.types import NodeInfo

logger = structlog.get_logger()


class SnapshotReplicator:
    """Manages segmenting, streaming, chunk verification, and reassembly."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        chunk_size_bytes: int = 16 * 1024,  # 16KB default
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus
        self._chunk_size = chunk_size_bytes

        # Active receiving sessions: session_id -> SnapshotTransferSession
        self._active_sessions: Dict[str, SnapshotTransferSession] = {}

    def chunk_snapshot(self, metadata: SnapshotMetadata, data: bytes) -> SnapshotManifest:
        """Partition snapshot bytes into uniform chunked payloads.

        Args:
            metadata: The snapshot metadata block.
            data: Raw serialized snapshot payload.

        Returns:
            The generated SnapshotManifest metadata block.
        """
        snapshot_id = metadata.snapshot_id
        chunks: List[bytes] = []
        checksums: List[str] = []

        total_bytes = len(data)
        offset = 0
        while offset < total_bytes:
            chunk = data[offset : offset + self._chunk_size]
            chunks.append(chunk)
            checksums.append(hashlib.sha256(chunk).hexdigest())
            offset += self._chunk_size

        return SnapshotManifest(
            snapshot_id=snapshot_id,
            metadata=metadata,
            total_chunks=len(chunks),
            chunk_size_bytes=self._chunk_size,
            checksums=checksums,
        )

    async def send_snapshot(
        self,
        peer: NodeInfo,
        metadata: SnapshotMetadata,
        data: bytes,
    ) -> None:
        """Incrementally transmit snapshot chunks to a remote peer.

        Args:
            peer: Remote destination NodeInfo.
            metadata: SnapshotMetadata description.
            data: Raw serialized snapshot payload.
        """
        manifest = self.chunk_snapshot(metadata, data)
        session_id = str(uuid.uuid4())

        await self._events.publish(
            "snapshot.transfer.started",
            {
                "session_id": session_id,
                "peer_id": peer.node_id,
                "snapshot_id": metadata.snapshot_id,
            },
        )

        offset = 0
        chunk_index = 0
        total_bytes = len(data)

        try:
            while offset < total_bytes:
                chunk_data = data[offset : offset + self._chunk_size]
                chunk_checksum = hashlib.sha256(chunk_data).hexdigest()

                chunk = SnapshotChunk(
                    snapshot_id=metadata.snapshot_id,
                    chunk_index=chunk_index,
                    data=chunk_data,
                    checksum=chunk_checksum,
                )

                payload = {
                    "session_id": session_id,
                    "chunk": chunk.model_dump(),
                    "manifest": manifest.model_dump(),
                }

                await self._bus.send(
                    peer,
                    MessageType.SNAPSHOT_CHUNK,
                    payload,
                    MessageMetadata(custom={"session_id": session_id}),
                )

                await self._events.publish(
                    "snapshot.chunk.sent",
                    {
                        "snapshot_id": metadata.snapshot_id,
                        "chunk_index": chunk_index,
                        "peer_id": peer.node_id,
                    },
                )

                chunk_index += 1
                offset += self._chunk_size
                await asyncio.sleep(0.005)  # Yield for loop to prevent network exhaustion

            # Notify transfer complete
            await self._bus.send(
                peer,
                MessageType.SNAPSHOT_TRANSFER_COMPLETE,
                {"session_id": session_id, "snapshot_id": metadata.snapshot_id},
            )
            await self._events.publish(
                "snapshot.transfer.completed",
                {
                    "session_id": session_id,
                    "peer_id": peer.node_id,
                    "snapshot_id": metadata.snapshot_id,
                },
            )

        except Exception as exc:
            await self._bus.send(
                peer,
                MessageType.SNAPSHOT_TRANSFER_FAILED,
                {"session_id": session_id, "error": str(exc)},
            )
            await self._events.publish(
                "snapshot.transfer.failed",
                {
                    "session_id": session_id,
                    "peer_id": peer.node_id,
                    "error": str(exc),
                },
            )
            raise SnapshotTransferError(f"Snapshot stream failed: {exc}") from exc

    def handle_chunk(
        self,
        session_id: str,
        chunk: SnapshotChunk,
        manifest: SnapshotManifest,
        peer_id: str,
    ) -> Optional[bytes]:
        """Receive, validate, reassemble snapshot chunk, returning full bytes if completed.

        Args:
            session_id: Session identifier.
            chunk: The SnapshotChunk received.
            manifest: SnapshotManifest detailing session expectations.
            peer_id: Source node ID.

        Returns:
            Reassembled bytes block if completed, else None.
        """
        # Validate chunk index bounds
        if chunk.chunk_index < 0 or chunk.chunk_index >= manifest.total_chunks:
            raise SnapshotChunkValidationError(
                f"Chunk index {chunk.chunk_index} out of range [0, {manifest.total_chunks})."
            )

        # Validate chunk checksum
        calculated = hashlib.sha256(chunk.data).hexdigest()
        if calculated != chunk.checksum:
            raise SnapshotChunkValidationError(f"Checksum mismatch in chunk {chunk.chunk_index}.")

        expected_checksum = manifest.checksums[chunk.chunk_index]
        if calculated != expected_checksum:
            raise SnapshotChunkValidationError(
                f"Chunk checksum does not match manifest registry at index {chunk.chunk_index}."
            )

        session = self._active_sessions.get(session_id)
        if not session:
            session = SnapshotTransferSession(
                session_id=session_id,
                snapshot_id=manifest.snapshot_id,
                peer_id=peer_id,
                total_chunks=manifest.total_chunks,
                next_chunk_index=0,
            )
            self._active_sessions[session_id] = session

        # Add chunk data
        session.chunks_received[chunk.chunk_index] = chunk.data

        # Fire event notification
        loop = asyncio.get_event_loop()
        loop.create_task(
            self._events.publish(
                "snapshot.chunk.received",
                {
                    "snapshot_id": manifest.snapshot_id,
                    "chunk_index": chunk.chunk_index,
                    "peer_id": peer_id,
                },
            )
        )

        # Check if reassembly completed
        if len(session.chunks_received) == session.total_chunks:
            # Reassemble full bytes block
            ordered_data = []
            for i in range(session.total_chunks):
                ordered_data.append(session.chunks_received[i])
            assembled_bytes = b"".join(ordered_data)

            # Re-verify full assembly checksum
            total_checksum = hashlib.sha256(assembled_bytes).hexdigest()
            if total_checksum != manifest.metadata.checksum:
                session.is_failed = True
                raise SnapshotChunkValidationError("Reassembled snapshot payload checksum mismatch.")

            session.is_completed = True
            # Cleanup session state
            del self._active_sessions[session_id]
            return assembled_bytes

        return None
