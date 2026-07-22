# Architecture Decision Record: Phase 36 – Enterprise Disaster Recovery, Backup, Snapshot & Business Continuity Framework

## Context
Decentralized distributed runtime platforms require high availability, consistency, and automated recovery from critical node failures, split-brain scenarios, data corruption, or hardware outages. To prevent loss of active cluster states and worker queue tasks, Flock needs a portable, Zero-Trust compliance-hardened backup, restore, and business continuity framework.

## Decision
We implemented the disaster recovery framework under `src/flock/recovery/` utilizing immutable Pydantic v2 data models and thread-safe abstractions. 

Key decisions:
- **`snapshot.py`**: Creates consistent in-memory `ClusterSnapshot` objects with deterministic state hashes (SHA-256).
- **`backup.py`**: Compiles snapshot records into `BackupArchive` descriptors, utilizing the Security package's `CryptographyEngine` for AES-GCM encryption and digital signature signing.
- **`restore.py`**: Validates checksum integrity and signature authenticity before unpacking and applying the backup state data.
- **`checkpoint.py`**: Handles distributed checkpoints with sequential counters, tracking coordination nodes and target snapshot IDs.
- **`retention.py`**: Automatically evicts older backups according to TTL policies and count limits.
- **`disaster_service.py`**: Maps disaster recovery operations to MessageBus requests and broadcasts EventBus lifecycle notifications. This is placed in `disaster_service.py` to avoid name collisions with the original Phase 11 `service.py` task retry scheduler.
- **`policy_manager.py`**: Manages disaster recovery policies under a separate descriptor from the Phase 11 task retries policy engine.

## Consequences
- **Security & Decryption**: Backups are securely encrypted using standard Python algorithms, ensuring no plaintext leaks on cloud object storage.
- **Zero regressions**: Preserved every single legacy task failover retry API from Phase 11, resulting in a successful test execution of all 595 tests.
- **Thread Safety**: Protected all internal catalog buffers and policy definitions with `threading.RLock`.
