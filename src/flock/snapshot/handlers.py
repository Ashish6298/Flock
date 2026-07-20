"""Network handlers for snapshot service."""

from __future__ import annotations

import json
from typing import Any
from flock.messaging.handlers import MessageHandler
from flock.messaging.models import MessageContext, MessageMetadata
from flock.protocol.packet import MessageType
from flock.snapshot.models import (
    SnapshotChunk,
    SnapshotInstallRequest,
    SnapshotInstallResponse,
    SnapshotManifest,
)
from flock.types import NodeInfo


class _InstallRequestHandler(MessageHandler):
    """Processes incoming SNAPSHOT_INSTALL_REQUEST."""

    def __init__(self, service: Any) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            req = SnapshotInstallRequest(**payload)
        except Exception:
            return

        # Record manifest details under temporary attributes for chunk handler
        self._service._current_install_req = req


class _ChunkHandler(MessageHandler):
    """Processes incoming SNAPSHOT_CHUNK segments."""

    def __init__(self, service: Any) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        session_id = payload.get("session_id")
        raw_chunk = payload.get("chunk")
        raw_manifest = payload.get("manifest")

        if not session_id or not raw_chunk or not raw_manifest:
            return

        try:
            chunk = SnapshotChunk(**raw_chunk)
            manifest = SnapshotManifest(**raw_manifest)
        except Exception:
            return

        # Process chunk reassembly
        assembled = self._service.replicator.handle_chunk(
            session_id=session_id,
            chunk=chunk,
            manifest=manifest,
            peer_id=context.sender.node_id,
        )

        if assembled:
            # Entire snapshot reassembled
            self._service._assembled_snapshot = (manifest.metadata, assembled)


class _TransferCompleteHandler(MessageHandler):
    """Processes SNAPSHOT_TRANSFER_COMPLETE notification."""

    def __init__(self, service: Any) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        session_id = payload.get("session_id")
        if not session_id:
            return

        assembled_tuple = getattr(self._service, "_assembled_snapshot", None)
        if not assembled_tuple:
            return

        metadata, data_bytes = assembled_tuple

        # Save to local storage
        self._service.storage.save_snapshot(metadata, data_bytes)

        # Restore State Machine atomically
        snapshot_data = json.loads(data_bytes.decode("utf-8"))
        
        # StateMachine service expects StateSnapshotMetadata schema
        from flock.statemachine.models import StateSnapshotMetadata
        fsm_metadata = StateSnapshotMetadata(
            applied_index=metadata.applied_index,
            current_term=metadata.current_term,
            timestamp=metadata.timestamp,
            checksum=metadata.checksum,
        )
        
        self._service._fsm.restore_snapshot(fsm_metadata, snapshot_data)

        # Also truncate/compact consensus log locally to match snapshot boundary
        self._service.compactor.compact(metadata.applied_index, metadata.current_term)

        # Send response confirmation back to leader
        reply_target = NodeInfo(
            node_id=context.sender.node_id,
            host=context.sender.host,
            port=context.sender.port,
        )

        resp = SnapshotInstallResponse(
            follower_id=self._service.node_id,
            term=self._service._consensus.get_current_term(),
            success=True,
            last_applied_index=metadata.applied_index,
        )

        await self._service._bus.send(
            reply_target,
            MessageType.SNAPSHOT_INSTALL_RESPONSE,
            resp.model_dump(),
        )

        # Publish event
        await self._service._events.publish(
            "snapshot.installed",
            {
                "snapshot_id": metadata.snapshot_id,
                "applied_index": metadata.applied_index,
            },
        )
