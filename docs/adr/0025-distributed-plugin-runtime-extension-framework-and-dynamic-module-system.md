# ADR 0025 – Distributed Plugin Runtime, Extension Framework & Dynamic Module System

**Date**: 2026-07-21  
**Status**: Accepted  
**Phase**: 25 – Distributed Plugin Runtime, Extension Framework & Dynamic Module System  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires a dynamic plugin framework enabling nodes to discover, load, validate, sandbox, and run custom extension models out-of-band without restarting core execution processes.

---

## Decision

We implement a complete **Distributed Plugin Runtime, Extension Framework & Dynamic Module System**:

1. **PluginRegistry**: Tracks active plugin manifests index directory list.
2. **PluginLoader**: Orchestrates load lifecycle hook registrations.
3. **PluginSandbox**: Verifies action execution permissions inside isolated contexts.
4. **PluginDependencyResolver**: Validates compatibility version guidelines and prevents cyclic dependency locks.
5. **PluginService**: Exposes query endpoints on the message bus.

---

## Consequences

- **Secure Execution**: Prevents plugin crashes from leaking into core loops via sandbox boundaries.
- **Topological Dependencies**: Guarantees prerequisite plugins activate in correct ordering maps.
- **Durable Configuration**: Preserves state configurations globally.
