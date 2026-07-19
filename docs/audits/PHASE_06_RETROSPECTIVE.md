# Phase 06 - Retrospective

## What Went Well
- **Separation of State Machines**: Maintaining the `HealthState` machine completely separate from the `ClusterMemberStatus` state machine inside the membership registry successfully decoupled membership tracking from connection dropouts.
- **Round-Trip Timing**: Calculating latency in milliseconds on receiving returns provided a direct pathway for future load balancing optimizations.

## Challenges & Solutions
- **Ephemeral Port Route Overrides**: Ephemerally mapped client connection channels during test iterations needed custom reply port overrides in metadata packets to route replies correctly.
- **Strict mypy typings**: Nested mock handlers inside test cases required explicit parameter mappings (`Dict[str, Any] -> None`) to comply with strict type validations.
