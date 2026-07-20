# ADR 0018 – Distributed Resource Manager & Intelligent Cluster Load Balancer

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 18 – Distributed Resource Manager & Intelligent Cluster Load Balancer  
**Milestone**: H – Cluster Operations & Resource Management  

---

## Context

Flock needs a decentralized resource orchestration mechanism to balance task assignments, limit cores/memory bounds, and forecast cluster saturation constraints without directly binding to local socket transports.

---

## Decision

We implement a complete **Distributed Resource Manager & Intelligent Cluster Load Balancer**:

1. **ResourceRegistry**: Tracks active CPU, memory, and accelerator metrics dynamically.
2. **ResourceAllocator**: Manages transactional bookings and release policies.
3. **LoadBalancingEngine**: Employs Best-Fit, Least Utilized, and Round Robin strategies.
4. **CapacityPlanner**: Extrapolates historical growth rate vectors to yield exhaustion warnings.
5. **AdmissionController**: Asserts limits, soft/hard caps, and node capacity fits.
6. **ResourceBalancer**: Detects loaded node skews, producing redistribution decisions.
7. **ResourceManagementService**: Exposes cluster utilization sync ports.

---

## Consequences

- **Resource-Aware Scheduling**: Tasks are directed to low-load nodes dynamically.
- **Quota Validation**: Prevents memory exhaustion or out-of-core errors from disrupting nodes.
- **Decoupled Mechanics**: Decouples metric scraping from specific system monitors.
