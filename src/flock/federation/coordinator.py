"""Federation Coordinator coordinates topologies, handshakes, policies, and health monitors."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Any
from flock.federation.exceptions import FederationError
from flock.federation.models import FederationCluster, FederationNode
from flock.federation.registry import FederationRegistry
from flock.federation.discovery import FederationDiscoveryService
from flock.federation.topology import FederationTopologyManager
from flock.federation.handshake import FederationHandshakeManager, FederationTrustStore
from flock.federation.policies import FederationPolicyManager
from flock.federation.health import FederationHealthMonitor
from flock.federation.metrics import FederationMetricsTracker
from flock.federation.audit import FederationAuditLogger
from flock.security.encryption import CryptographyEngine


class FederationCoordinator:
    """Consolidates cross-cluster discovery registries, policy managers, and latency-routing controllers."""

    def __init__(
        self,
        local_cluster_id: str,
        crypto: CryptographyEngine,
    ) -> None:
        self.local_cluster_id = local_cluster_id
        self._lock = threading.RLock()
        
        # Core engines wiring
        self.registry = FederationRegistry()
        self.discovery = FederationDiscoveryService(local_cluster_id)
        self.topology = FederationTopologyManager(local_cluster_id)
        self.handshake = FederationHandshakeManager(local_cluster_id, crypto)
        self.trust = FederationTrustStore(local_cluster_id)
        self.policy = FederationPolicyManager()
        self.health = FederationHealthMonitor()
        self.metrics = FederationMetricsTracker()
        self.audit = FederationAuditLogger()

    def register_federated_cluster(
        self,
        cluster: FederationCluster,
        trust_signature: str,
        certificate_pem: str,
    ) -> None:
        """Register remote cluster into registry and trust store."""
        with self._lock:
            # 1. Register cluster in registry
            self.registry.register_cluster(cluster)
            
            # 2. Reconstruct Trust relationship
            # Since handshake verification might occur dynamically on join packets,
            # this method acts as the registry persistence endpoint.
            from flock.federation.models import TrustRelationship
            import time
            
            trust = TrustRelationship(
                local_cluster_id=self.local_cluster_id,
                remote_cluster_id=cluster.cluster_id,
                certificate_pem=certificate_pem,
                signature=trust_signature,
                established_at=time.time(),
                valid_until=time.time() + 86400.0,
            )
            self.trust.register_trust(trust)
            self.topology.register_cluster(cluster)
            self.health.set_cluster_health(cluster.cluster_id, cluster.is_healthy)
            
            # Audit log
            self.audit.log_event(
                "cluster.registered",
                {"cluster_id": cluster.cluster_id, "name": cluster.name}
            )
