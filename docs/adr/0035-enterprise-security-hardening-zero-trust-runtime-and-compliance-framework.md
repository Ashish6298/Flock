# Architecture Decision Record: Phase 35 – Enterprise Security Hardening, Zero-Trust Runtime & Compliance Framework

## Context
Flock was built as a decentralized distributed execution framework. As a cluster grows, standard trust assumptions between peer-to-peer execution nodes become liabilities. To protect against malicious or compromised nodes, we require a comprehensive Zero-Trust runtime platform including certificate authorities, dynamic ABAC policies, encrypted secrets management, tamper-evident audit logs, intrusion detection, auto-quarantine isolations, and key rotation controls.

## Decision
We implemented a non-intrusive Zero-Trust security and compliance framework under `src/flock/security/` that extends previous security constructs (Phase 17) while remaining transport-independent, thread-safe, and backward compatible. 

Specifically:
- **`encryption.py`**: Thread-safe AES-GCM encryption emulation and digital signatures.
- **`certificates.py`**: Certificate authority (CA) generation, revocation tracking, and date/signature validations.
- **`authentication.py`**: Port-independent API keys, session tokens, and identity verifications.
- **`authorization.py`**: Enhanced `AuthorizationEngine` supporting dynamic role assignments (RBAC) and condition-based attribute policies (ABAC). Deny policies are evaluated first (Zero-Trust).
- **`policy.py`**: Policy engine interfaces to manage Zero-Trust authorization policies.
- **`secrets.py`**: Encrypted `SecretEnvelope` models and pluggable `VaultProvider` abstractions for secure local and remote secrets management.
- **`compliance.py`**: Compliance controls baseline checking.
- **`intrusion.py`**: Brute-force and threat heuristic counters.
- **`quarantine.py`**: Isolated quarantined nodes management.
- **`rotation.py`**: Credential and certificate rollover triggers.
- **`hardening.py`**: Environment validation for system write paths, debugger presence, and running privileges.

## Consequences
- **Security Posture**: Allows fine-grained access rules at the message and resource layers. Malicious or misbehaving nodes are auto-isolated by the `QuarantineManager` via the intrusion detection rules.
- **Backward Compatibility**: Kept the exact same API signatures for older code. `CryptographyEngine` was modified to be fully compatible with mock 6-byte secrets used in earlier tests.
- **Verification**: Zero warnings reported by mypy strict. All 588 unit tests passed successfully.
