# ADR 0024 – Distributed API Gateway, REST/gRPC Interface & Developer SDK Framework

**Date**: 2026-07-21  
**Status**: Accepted  
**Phase**: 24 – Distributed API Gateway, REST/gRPC Interface & Developer SDK Framework  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires an external REST and gRPC API gateway platform enabling applications, CLI endpoints, and SDK clients to invoke actions inside the cluster without exposing internal Raft network sockets.

---

## Decision

We implement a complete **Distributed API Gateway, REST/gRPC Interface & Developer SDK Framework**:

1. **ApiRouter**: Directs incoming requests matching method and path patterns.
2. **RequestValidator**: Validates payload schemas and JSON boundaries.
3. **ResponseSerializer**: Serializes data to JSON format.
4. **ApiGateway**: Enforces rate limiting, token keys, and security validation.
5. **OpenApiGenerator**: Dynamically generates OpenAPI documents from route configurations.
6. **SdkGenerator**: Generates Python client wrapper definitions.
7. **ApiService**: Handles API request sync endpoints on the MessageBus.

---

## Consequences

- **Secure Gateways**: Enforces token authentication and IP throttling boundaries.
- **Developer Usability**: Exposes Swagger documents and generates clean SDK bindings dynamically.
- **Clean Architecture**: API endpoints are separated from transport loops.
