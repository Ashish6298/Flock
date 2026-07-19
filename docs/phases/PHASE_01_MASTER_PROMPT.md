# Phase 1 Master Prompt

## Objective
Initialize the repository setup, directory layouts, and foundational configuration/architecture abstractions for Flock.

## Scope
- Create standard `pyproject.toml` and basic configurations.
- Design base exception classes subclassing `FlockError`.
- Define common primitive types (`NodeInfo`, `TaskSpec`, `TaskStatus`).
- Implement the core generic interfaces (`Serializer`, `Transport`, `Discovery`).
- Create `ClusterConfig` configuration mapping schemas using Pydantic.
