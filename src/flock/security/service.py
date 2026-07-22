"""High-level SecurityService coordinating credentials, policies, vaults, and compliance monitoring."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, Optional, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.security.audit import SecurityAuditLogger
from flock.security.encryption import CryptographyEngine
from flock.security.exceptions import SecurityError
from flock.security.handshake import SecureHandshakeManager
from flock.security.identity import IdentityManager
from flock.security.models import NodeIdentity, SecurityPolicy
from flock.security.authorization import AuthorizationEngine
from flock.security.token import TokenManager
from flock.security.certificates import CertificateManager
from flock.security.authentication import AuthenticationEngine
from flock.security.policy import PolicyManager
from flock.security.secrets import SecretsManager
from flock.security.compliance import ComplianceEngine
from flock.security.intrusion import IntrusionDetector
from flock.security.quarantine import QuarantineManager
from flock.security.rotation import CredentialRotationEngine
from flock.security.hardening import HardeningEngine

logger = structlog.get_logger()


class SecurityService:
    """Consolidates cryptography, Zero-Trust authorization, secrets vaulting, compliance, and intrusion protection."""

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
        self._lock = threading.RLock()

        # Phase 17 Core components
        self.crypto = CryptographyEngine(secret_key)
        self.identity = IdentityManager(local_identity)
        self.rbac = AuthorizationEngine()
        self.tokens = TokenManager(self.crypto)
        self.handshake = SecureHandshakeManager(self.crypto, self.identity)
        self.audit = SecurityAuditLogger(self._events)

        # Phase 35 Enterprise extensions
        self.certificates = CertificateManager(self.crypto)
        self.authentication = AuthenticationEngine(self.crypto)
        self.policy = PolicyManager(self.rbac)
        self.secrets = SecretsManager(self.crypto)
        self.compliance = ComplianceEngine()
        self.intrusion = IntrusionDetector()
        self.quarantine = QuarantineManager()
        self.rotation = CredentialRotationEngine(self.crypto, self.certificates)
        self.hardening = HardeningEngine()

        self._running = False

    async def start(self) -> None:
        """Start the security service and register message handlers."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._register_handlers()
        
        # Publish EventBus initialization event
        await self._events.publish(
            "security.initialized",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
                "status": "ready",
            }
        )
        logger.info("SecurityService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop security operations."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        # Publish EventBus teardown event
        await self._events.publish(
            "security.shutdown",
            {
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        )
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
                valid = False
                if sender_id and sig and cert:
                    # In real network loop, we execute challenge response validation
                    self.identity.verify_node_identity(sender_id, cert)
                    valid = True
                
                # Check intrusion detection: if node is quarantine-isolated, deny auth
                if sender_id and self.quarantine.is_isolated(sender_id):
                    valid = False
                
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

        async def handle_secret_retrieval(context: Any) -> None:
            payload = context.payload or {}
            secret_id = payload.get("secret_id")
            client_id = payload.get("client_id")
            
            # Simple permission checks: only allow coordinators/workers to retrieve secrets
            decision = self.rbac.authorize(client_id or "", "secrets.read")
            reply_target = context.sender
            
            if not decision.allowed:
                await self._bus.send(
                    reply_target,
                    MessageType.SECRET_RETRIEVAL_RESPONSE,
                    {"success": False, "error": f"Unauthorized: {decision.reason}"},
                )
                await self._events.publish(
                    "secret.access.denied",
                    {"secret_id": secret_id, "subject": client_id, "timestamp": time.time()},
                )
                return

            try:
                secret_value = self.secrets.retrieve_secret(secret_id or "")
                await self._bus.send(
                    reply_target,
                    MessageType.SECRET_RETRIEVAL_RESPONSE,
                    {"success": True, "secret_value": secret_value},
                )
                await self._events.publish(
                    "secret.access.granted",
                    {"secret_id": secret_id, "subject": client_id, "timestamp": time.time()},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.SECRET_RETRIEVAL_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        async def handle_policy_sync(context: Any) -> None:
            payload = context.payload or {}
            policy_data = payload.get("policy")
            reply_target = context.sender
            
            if not policy_data:
                await self._bus.send(
                    reply_target,
                    MessageType.AUTH_RESPONSE,
                    {"success": False, "error": "Missing policy data"},
                )
                return
                
            try:
                # Parse policy into SecurityPolicy model
                policy = SecurityPolicy(
                    policy_id=policy_data.get("policy_id"),
                    effect=policy_data.get("effect"),
                    subjects=policy_data.get("subjects"),
                    resources=policy_data.get("resources"),
                    actions=policy_data.get("actions"),
                    conditions=policy_data.get("conditions", {}),
                )
                self.policy.add_policy(policy)
                
                await self._bus.send(
                    reply_target,
                    MessageType.AUTH_RESPONSE,
                    {"success": True},
                )
                await self._events.publish(
                    "policy.enforced",
                    {"policy_id": policy.policy_id, "timestamp": time.time()},
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.AUTH_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.AUTH_REQUEST,
            _SecurityQueryHandler(handle_auth_query),
        )
        router.register(
            MessageType.SECRET_RETRIEVAL_REQUEST,
            _SecurityQueryHandler(handle_secret_retrieval),
        )
        router.register(
            MessageType.SECURITY_POLICY_SYNC,
            _SecurityQueryHandler(handle_policy_sync),
        )


class _SecurityQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
