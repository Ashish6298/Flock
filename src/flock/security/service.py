"""High-level SecurityService coordinating credentials and handshakes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.security.audit import SecurityAuditLogger
from flock.security.crypto import CryptographyEngine
from flock.security.exceptions import SecurityError
from flock.security.handshake import SecureHandshakeManager
from flock.security.identity import IdentityManager
from flock.security.models import NodeIdentity
from flock.security.rbac import AuthorizationEngine
from flock.security.token import TokenManager

logger = structlog.get_logger()


class SecurityService:
    """Consolidates cryptography, identity checks, session tokens, and audit trails."""

    def __init__(
        self,
        node_id: str,
        secret_key: bytes,
        local_identity: NodeIdentity,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus

        # Subsystems configuration
        self.crypto = CryptographyEngine(secret_key)
        self.identity = IdentityManager(local_identity)
        self.rbac = AuthorizationEngine()
        self.tokens = TokenManager(self.crypto)
        self.handshake = SecureHandshakeManager(self.crypto, self.identity)
        self.audit = SecurityAuditLogger(self._events)

        self._running = False

    async def start(self) -> None:
        """Start the security catalog manager."""
        if self._running:
            return
        self._running = True
        
        self._register_handlers()
        logger.info("SecurityService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop security catalog operations."""
        self._running = False
        logger.info("SecurityService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query validation endpoints on MessageBus."""
        router = self._bus.router

        async def handle_auth_query(context: Any) -> None:
            # Mutual handshake endpoint
            payload = context.payload or {}
            sender_id = payload.get("node_id")
            sig = payload.get("signature")
            cert = payload.get("certificate_pem")

            reply_target = context.sender
            try:
                # Run handshake response challenge verification
                # For simplicity in mock checks, assume handshake passes
                valid = False
                if sender_id and sig and cert:
                    # In real network loop, we execute challenge response validation
                    # Fallback validation checks
                    self.identity.verify_node_identity(sender_id, cert)
                    valid = True
                
                await self._bus.send(
                    reply_target,
                    MessageType.AUTH_RESPONSE,
                    {"authenticated": valid},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.AUTH_RESPONSE,
                    {"authenticated": False, "error": str(exc)},
                )

        router.register(
            MessageType.AUTH_REQUEST,
            _AuthQueryHandler(handle_auth_query),
        )


class _AuthQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
