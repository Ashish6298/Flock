"""Unit tests for Phase 35 Zero-Trust Security, Hardening & Compliance Subsystem."""

import time
import pytest
from typing import Any
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.security.exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    SignatureVerificationError,
    TokenExpiredError,
    KeyRotationError,
    PolicyEvaluationError,
    CertificateValidationError,
    SecretStorageError,
    ComplianceControlError,
    QuarantineError,
)
from flock.security.models import (
    NodeIdentity,
    SessionToken,
    AccessDecision,
    SecurityPolicy,
    CertificateDetails,
    SecretEnvelope,
    ComplianceReport,
    QuarantineStatus,
)
from flock.security.encryption import CryptographyEngine
from flock.security.certificates import CertificateManager
from flock.security.authentication import AuthenticationEngine
from flock.security.authorization import AuthorizationEngine
from flock.security.policy import PolicyManager
from flock.security.secrets import SecretsManager, InMemoryVaultProvider
from flock.security.compliance import ComplianceEngine
from flock.security.intrusion import IntrusionDetector
from flock.security.quarantine import QuarantineManager
from flock.security.rotation import CredentialRotationEngine
from flock.security.hardening import HardeningEngine
from flock.security.service import SecurityService


# -----------------------------------------------------------------------------
# Cryptography & Encryption Tests
# -----------------------------------------------------------------------------

def test_cryptography_engine_aes_gcm() -> None:
    secret = b"key_must_be_at_least_16_bytes_long"
    crypto = CryptographyEngine(secret)
    
    plaintext = "Sensitive data to encrypt"
    ciphertext, iv, tag = crypto.encrypt_aes_gcm(plaintext)
    
    # Decrypt and verify
    decrypted = crypto.decrypt_aes_gcm(ciphertext, iv, tag)
    assert decrypted == plaintext


def test_cryptography_engine_aes_gcm_auth_tag_mismatch() -> None:
    secret = b"key_must_be_at_least_16_bytes_long"
    crypto = CryptographyEngine(secret)
    ciphertext, iv, tag = crypto.encrypt_aes_gcm("test")
    
    # Decrypt with wrong tag
    with pytest.raises(SecurityError, match="integrity verification failed"):
        crypto.decrypt_aes_gcm(ciphertext, iv, "invalid_tag_hex_digest")


def test_cryptography_engine_digital_signatures() -> None:
    secret = b"key_must_be_at_least_16_bytes_long"
    crypto = CryptographyEngine(secret)
    
    data = b"Some data blocks"
    sig = crypto.sign_data(data)
    
    # Verification should pass
    crypto.verify_signature(data, sig)
    
    # Verification should fail with wrong data
    with pytest.raises(SignatureVerificationError):
        crypto.verify_signature(data + b"modified", sig)


# -----------------------------------------------------------------------------
# Certificates & Trust Chains Tests
# -----------------------------------------------------------------------------

def test_certificate_lifecycle() -> None:
    secret = b"ca_secret_key_must_be_16_bytes"
    crypto = CryptographyEngine(secret)
    cert_mgr = CertificateManager(crypto)
    
    # Issue cert
    cert = cert_mgr.issue_certificate("node-2", validity_days=10)
    assert cert.subject == "node-2"
    
    # Validate cert
    assert cert_mgr.validate_certificate(cert) is True
    
    # Revoke cert
    cert_mgr.revoke_certificate(cert.serial_number)
    assert cert_mgr.is_revoked(cert.serial_number) is True
    
    with pytest.raises(CertificateValidationError, match="revoked"):
        cert_mgr.validate_certificate(cert)


# -----------------------------------------------------------------------------
# Authentication Engine Tests
# -----------------------------------------------------------------------------

def test_api_key_authentication() -> None:
    secret = b"auth_secret_key_must_be_16_bytes"
    crypto = CryptographyEngine(secret)
    auth_eng = AuthenticationEngine(crypto)
    
    auth_eng.register_api_key("api-key-12345", "dashboard-client")
    assert auth_eng.authenticate_api_key("api-key-12345") == "dashboard-client"
    
    with pytest.raises(AuthenticationError):
        auth_eng.authenticate_api_key("invalid-key")


# -----------------------------------------------------------------------------
# Authorization & Zero-Trust Policies Tests
# -----------------------------------------------------------------------------

def test_rbac_and_abac_authorization() -> None:
    auth_eng = AuthorizationEngine()
    
    # RBAC assign role
    auth_eng.assign_role("node-1", "worker")
    
    # Allow permission check
    dec = auth_eng.authorize("node-1", "tasks.execute")
    assert dec.allowed is True
    
    # Denied permission check
    dec = auth_eng.authorize("node-1", "tasks.create")
    assert dec.allowed is False
    
    # ABAC dynamic policy add
    policy = SecurityPolicy(
        policy_id="abac-1",
        effect="allow",
        subjects=["node-*"],
        resources=["tasks/*"],
        actions=["tasks.create"],
        conditions={"environment": "production"},
    )
    auth_eng.add_policy(policy)
    
    # Authorize with attributes matching ABAC condition
    dec = auth_eng.authorize("node-5", "tasks.create", attributes={"environment": "production"})
    assert dec.allowed is True
    
    # Authorize with attributes NOT matching condition
    dec = auth_eng.authorize("node-5", "tasks.create", attributes={"environment": "development"})
    assert dec.allowed is False


# -----------------------------------------------------------------------------
# Secrets Manager & Vault Tests
# -----------------------------------------------------------------------------

def test_secrets_manager_vault() -> None:
    secret = b"vault_secret_key_must_be_16_bytes"
    crypto = CryptographyEngine(secret)
    vault = InMemoryVaultProvider()
    sec_mgr = SecretsManager(crypto, vault)
    
    # Store secret
    envelope = sec_mgr.store_secret("db.password", "supersecret123")
    assert envelope.secret_id == "db.password"
    
    # Retrieve secret
    value = sec_mgr.retrieve_secret("db.password")
    assert value == "supersecret123"
    
    # Delete secret
    sec_mgr.delete_secret("db.password")
    with pytest.raises(SecretStorageError):
        sec_mgr.retrieve_secret("db.password")


# -----------------------------------------------------------------------------
# Compliance Engine Tests
# -----------------------------------------------------------------------------

def test_compliance_engine() -> None:
    comp = ComplianceEngine()
    
    # Run initial audit (100% compliant by default)
    rep = comp.run_compliance_audit()
    assert rep.score == 100.0
    
    # Set control to false
    comp.set_control_status("SEC-001", False)
    rep = comp.run_compliance_audit()
    assert rep.score == 75.0
    assert "SEC-001" in rep.failed_controls
    assert "SEC-001" in rep.remediations


# -----------------------------------------------------------------------------
# Intrusion Detection Tests
# -----------------------------------------------------------------------------

def test_intrusion_detector() -> None:
    detector = IntrusionDetector(failure_threshold=3, window_seconds=10)
    
    # 2 failures -> not blacklisted
    assert detector.record_auth_failure("attacker-node") is False
    assert detector.record_auth_failure("attacker-node") is False
    assert detector.is_blacklisted("attacker-node") is False
    
    # 3rd failure -> blacklisted
    assert detector.record_auth_failure("attacker-node") is True
    assert detector.is_blacklisted("attacker-node") is True
    assert len(detector.list_incidents()) == 1


# -----------------------------------------------------------------------------
# Quarantine Manager Tests
# -----------------------------------------------------------------------------

def test_quarantine_manager() -> None:
    qm = QuarantineManager()
    
    # Quarantine node
    status = qm.quarantine_node("node-bad", "unusual rate of queries", duration_seconds=5)
    assert status.isolated is True
    assert qm.is_isolated("node-bad") is True
    
    # Recover node
    recovered = qm.recover_node("node-bad")
    assert recovered.isolated is False
    assert qm.is_isolated("node-bad") is False


# -----------------------------------------------------------------------------
# Credential Rotation Tests
# -----------------------------------------------------------------------------

def test_credential_rotation() -> None:
    crypto = CryptographyEngine(b"rotation_secret_key_16bytes")
    cert_mgr = CertificateManager(crypto)
    engine = CredentialRotationEngine(crypto, cert_mgr)
    
    rotated_events = []
    engine.add_rotation_listener("encryption_key", lambda ev, item: rotated_events.append(item))
    
    new_secret = b"new_secret_key_value_16bytes"
    engine.rotate_encryption_key("v2", new_secret)
    
    assert "v2" in rotated_events
    assert engine.get_last_rotation_time("encryption_key") is not None


# -----------------------------------------------------------------------------
# Hardening Engine Tests
# -----------------------------------------------------------------------------

def test_hardening_engine() -> None:
    he = HardeningEngine()
    warnings = he.verify_runtime_safety()
    
    status = he.get_status()
    assert "least_privilege" in status
    assert "path_safety" in status


# -----------------------------------------------------------------------------
# Security Service Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_security_service_integration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_init(data: Any) -> None:
        event_list.append(data)
        
    events.subscribe("security.initialized", on_init)
    
    local_id = NodeIdentity(node_id="coordinator-1", public_key="pubkey", certificate_pem="certpem")
    service = SecurityService("coordinator-1", b"secret_key_16bytes_long", local_id, bus, events)
    
    await service.start()
    assert service._running is True
    assert len(event_list) == 1
    
    # Verify routes registered
    assert service._bus.router.register.call_count == 3
    
    await service.stop()
    assert service._running is False
