"""Getting started with Flock: 5 Minute Cluster creation and Task execution."""

import asyncio
from unittest.mock import MagicMock
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.consensus import ConsensusService
from flock.controlplane.service import ControlPlaneService
from flock.controlplane.models import EnrolledCluster


async def main() -> None:
    # 1. Initialize Messaging & Event components
    events = EventBus()
    
    # Quick mocks
    transport = MagicMock()
    serializer = MagicMock()
    message_bus = MessageBus(transport, serializer)

    # 2. Wire Control Plane & Subsystems
    cp_service = ControlPlaneService(node_id="coordinator-node", message_bus=message_bus, event_bus=events)
    await cp_service.start()

    # 3. Register a cluster member
    cluster = EnrolledCluster(
        cluster_id="cluster-east",
        fleet_id="fleet-prod",
        name="US East compute",
        version="1.0.0",
        labels={"region": "east"},
        features_active=["Consensus"],
        last_seen=0.0
    )
    cp_service.coordinator.clusters.enroll_cluster(cluster)
    print(f"Successfully initialized Flock Cluster: {cluster.name} under organization registries.")

    await cp_service.stop()

if __name__ == "__main__":
    asyncio.run(main())
