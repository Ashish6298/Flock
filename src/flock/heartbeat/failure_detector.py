"""Logical component tracking missed windows and evaluating reachability state changes."""

import time
import structlog
from typing import Optional
from flock.events.bus import EventBus
from flock.heartbeat.models import HealthRecord, HealthState
from flock.heartbeat.registry import HealthRegistry

logger = structlog.get_logger()

class FailureDetector:
    """Evaluates metrics and transitions cluster node reachability states."""

    def __init__(
        self,
        registry: HealthRegistry,
        event_bus: EventBus,
        ping_timeout_sec: float = 1.0,
        max_missed_count: int = 3
    ) -> None:
        self.registry = registry
        self.events = event_bus
        self.ping_timeout = ping_timeout_sec
        self.max_missed = max_missed_count

    async def record_heartbeat_success(self, node_id: str, rtt_ms: float = 0.0) -> None:
        """Mark successful response and transition back to healthy states."""
        now = time.time()
        existing = self.registry.get_record(node_id)
        
        if not existing:
            record = HealthRecord(
                node_id=node_id,
                state=HealthState.HEALTHY,
                last_heartbeat_timestamp=now,
                round_trip_time_ms=rtt_ms
            )
            self.registry.set_record(record)
            await self.events.publish("heartbeat.node_healthy", {"node_id": node_id})
            return

        old_state = existing.state
        new_state = HealthState.HEALTHY

        if old_state in (HealthState.SUSPECTED, HealthState.UNREACHABLE):
            new_state = HealthState.RECOVERING

        record = HealthRecord(
            node_id=node_id,
            state=new_state,
            last_heartbeat_timestamp=now,
            missed_heartbeats_count=0,
            round_trip_time_ms=rtt_ms,
            sequence_id=existing.sequence_id + 1
        )
        self.registry.set_record(record)

        if old_state != new_state:
            if new_state == HealthState.RECOVERING:
                await self.events.publish("heartbeat.node_recovering", {"node_id": node_id})
                # Immediately upgrade recovering to healthy if direct checks confirm reachability
                record_healthy = HealthRecord(
                    node_id=node_id,
                    state=HealthState.HEALTHY,
                    last_heartbeat_timestamp=now,
                    missed_heartbeats_count=0,
                    round_trip_time_ms=rtt_ms,
                    sequence_id=record.sequence_id + 1
                )
                self.registry.set_record(record_healthy)
                await self.events.publish("heartbeat.node_healthy", {"node_id": node_id})
            else:
                await self.events.publish("heartbeat.node_healthy", {"node_id": node_id})

    async def evaluate_node(self, node_id: str) -> None:
        """Evaluate timeouts and advance failure suspect states."""
        now = time.time()
        record = self.registry.get_record(node_id)
        if not record:
            return

        elapsed = now - record.last_heartbeat_timestamp
        if elapsed > self.ping_timeout:
            missed = record.missed_heartbeats_count + 1
            new_state = record.state

            if missed >= self.max_missed:
                new_state = HealthState.UNREACHABLE
            elif missed >= 1:
                new_state = HealthState.SUSPECTED

            updated = HealthRecord(
                node_id=node_id,
                state=new_state,
                last_heartbeat_timestamp=record.last_heartbeat_timestamp,
                missed_heartbeats_count=missed,
                round_trip_time_ms=record.round_trip_time_ms,
                sequence_id=record.sequence_id
            )
            self.registry.set_record(updated)

            if record.state != new_state:
                if new_state == HealthState.SUSPECTED:
                    await self.events.publish("heartbeat.node_suspected", {"node_id": node_id})
                elif new_state == HealthState.UNREACHABLE:
                    await self.events.publish("heartbeat.node_unreachable", {"node_id": node_id})
