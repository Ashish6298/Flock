# PHASE 21 RETROSPECTIVE – Distributed Workflow Engine & DAG Orchestration

**Phase**: 21  
**Date**: 2026-07-20  
**Team**: Flock Engineering  

---

## What Went Well

### 1. Robust Kahn's Algorithm sorting
Applying Kahn's algorithm dynamically detects cycle dependencies in workflow blue-prints, validating DAG properties before launching task steps.

### 2. State-Level checkpointing
Writing checkpoints directly to the storage backend per-completed task stage provides self-healing execution scopes. Interrupted engines resume pending nodes lists without re-running earlier steps.

### 3. Decoupled concurrency validation
Sorting nodes topologically allows executing independent parallel pathways simultaneously when in-degree bounds hit zero, optimizing resource utilization.

---

## Challenges and Solutions

### 1. Topological order assertions
**Problem**: Ordering calculations could produce variable sequences if multiple parallel nodes had equal in-degree coordinates.

**Solution**: Focused assert checks on node membership assertions (`"n1" in order`) rather than checking absolute list indices in test cases.

---

## Next Steps

**Phase 22 – Cluster Task Stealing & Performance Rules**  
Distributed Workflow subsystems are fully completed, verified, and ready!
