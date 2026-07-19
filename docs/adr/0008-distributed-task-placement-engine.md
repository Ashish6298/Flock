# ADR 0008: Distributed Task Placement Engine

## Context & Problem Statement
With task scheduler, cluster membership, and node heartbeats operational, Flock needs a transport-independent Task Placement Engine. The engine must evaluate healthy cluster members, match resource capabilities and constraint parameters, prioritize candidate node targets using scoring algorithms, and map task assignments securely across the messaging protocol.

## Selected Solution
We implement:
1. **NodeCapability**: Immutable resource specifications (CPU architectures, operating systems, logical counts, custom tags).
2. **PlacementDecision** & **AssignmentRecord**: Immutable records detailing task placement selection parameters.
3. **PlacementRegistry**: Catalog tracking assigned task ownership targets.
4. **PlacementEngine**: Validates target nodes against task capability tags (e.g. GPU, linux) and assigns task ownership via dynamic handshake RPCs (`TASK_ASSIGN`, `TASK_ASSIGN_ACK`).

## Consequences & Trade-offs
- Task placement decisions are calculated independently of task execution.
- Baseline FIRST_HEALTHY capability matching satisfies Milestone C, preparing extensions for Round-Robin or Least-Loaded placement policies in future scheduling phases.
