"""Unit tests for Phase 37 Enterprise Multi-Cloud Federation, Hybrid Cluster Management & Cross-Region Orchestration Subsystem."""

import time
import pytest
from unittest.mock import MagicMock, AsyncMock

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.security.encryption import CryptographyEngine
from flock.federation.exceptions import (
    FederationError,
    TrustVerificationError,
    TopologyDiscoveryError,
    FederationPolicyViolationError,
)
from flock.federation.models import (
    FederationCluster,
    FederationNode,
    TrustRelationship,
    FederationTopology,
    FederationPolicy,
)
from flock.federation.discovery import FederationDiscoveryService
from flock.federation.topology import FederationTopologyManager
from flock.federation.handshake import FederationHandshakeManager, FederationTrustStore
from flock.federation.policies import FederationPolicyManager
from flock.federation.health import FederationHealthMonitor
from flock.federation.metrics import FederationMetricsTracker
from flock.federation.audit import FederationAuditLogger
from flock.federation.coordinator import FederationCoordinator
from flock.federation.enterprise_service import EnterpriseFederationService


# -----------------------------------------------------------------------------
# Discovery & Topology Tests
# -----------------------------------------------------------------------------

def test_federation_discovery() -> None:
    svc = FederationDiscoveryService("us-east")
    ad = svc.publish_advertisement({"cpu_idle": 80.0, "ram_idle": 64.0})
    
    assert ad.cluster_id == "us-east"
    assert ad.resource_summary["cpu_idle"] == 80.0
    
    svc.register_remote_advertisement(ad)
    assert "us-east" in svc.list_discovered_clusters()
    assert svc.get_advertisement("us-east").cluster_id == "us-east"


def test_federation_topology() -> None:
    mgr = FederationTopologyManager("us-west")
    c1 = FederationCluster(cluster_id="c-1", name="cluster-1", endpoints=["1.1.1.1"], is_healthy=True, capacity_score=0.8)
    mgr.register_cluster(c1)
    
    # Latency updates
    mgr.update_link_latency("us-west", "c-1", 45.2)
    assert mgr.get_link_latency("us-west", "c-1") == 45.2
    
    # Check default latency
    assert mgr.get_link_latency("us-west", "c-nonexistent") == 10.0
    
    top = mgr.get_topology()
    assert len(top.clusters) == 1
    assert top.clusters[0].cluster_id == "c-1"


# -----------------------------------------------------------------------------
# Handshake & Trust Store Tests
# -----------------------------------------------------------------------------

def test_secure_federation_handshake() -> None:
    crypto = CryptographyEngine(b"federation_signing_secret_16bytes")
    hs_mgr = FederationHandshakeManager("us-east", crypto)
    
    nonce = hs_mgr.generate_handshake_challenge("eu-central")
    assert nonce is not None
    
    # Sign challenge response simulating remote eu-central cluster
    sig = crypto.generate_hmac(f"eu-central:{nonce}".encode("utf-8"))
    
    trust = hs_mgr.verify_handshake_response("eu-central", sig, "cert_pem_data")
    assert trust.local_cluster_id == "us-east"
    assert trust.remote_cluster_id == "eu-central"
    
    store = FederationTrustStore("us-east")
    store.register_trust(trust)
    assert store.is_trusted("eu-central") is True


# -----------------------------------------------------------------------------
# Policy Evaluation Tests
# -----------------------------------------------------------------------------

def test_routing_policy_verification() -> None:
    pm = FederationPolicyManager()
    
    # Register latency limit policy for remote cluster
    policy = FederationPolicy(
        policy_id="latency-policy",
        target_clusters=["eu-central"],
        allowed_actions=["tasks.execute"],
        max_cross_region_latency_ms=100.0,
    )
    pm.register_policy(policy)
    
    # Under boundary -> success
    assert pm.validate_routing_policy("tasks.execute", "us-east", "eu-central", 45.0) is True
    
    # Latency exceeded -> policy violation error
    with pytest.raises(FederationPolicyViolationError, match="Latency boundary violated"):
        pm.validate_routing_policy("tasks.execute", "us-east", "eu-central", 120.0)


# -----------------------------------------------------------------------------
# Health and Metrics Tests
# -----------------------------------------------------------------------------

def test_health_monitor() -> None:
    hm = FederationHealthMonitor()
    hm.set_cluster_health("c1", True)
    hm.set_cluster_health("c2", False)
    
    report = hm.get_health_report()
    assert report.status == "DEGRADED"
    assert report.cluster_healths["c1"] is True
    assert report.cluster_healths["c2"] is False


def test_metrics_tracker() -> None:
    tracker = FederationMetricsTracker()
    tracker.record_remote_execution()
    tracker.record_failover(success=True)
    tracker.update_replication_delay(1.5)
    
    rep = tracker.generate_report(active_clusters_count=3)
    assert rep.active_clusters_count == 3
    assert rep.remote_executions_count == 1
    assert rep.failover_success_count == 1
    assert rep.replication_delay_seconds == 1.5


# -----------------------------------------------------------------------------
# Enterprise Federation Service Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enterprise_federation_service() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    bus.send = AsyncMock()
    
    events = EventBus()
    event_list = []
    
    async def on_join(data: dict) -> None: # type: ignore[type-arg]
        event_list.append(data)
        
    events.subscribe("federation.cluster.joined", on_join)
    
    crypto = CryptographyEngine(b"federation_service_secret_16bytes")
    service = EnterpriseFederationService("us-east", crypto, bus, events)
    
    await service.start()
    assert service._running is True
    
    # Verify MessageBus registration
    assert service._bus.router.register.call_count == 2
    
    await service.stop()
    assert service._running is False
