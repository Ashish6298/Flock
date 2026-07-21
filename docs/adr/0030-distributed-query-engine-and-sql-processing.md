# ADR 0030 – Distributed Query Engine, SQL Processing & Analytics Framework

**Date**: 2026-07-21  
**Status**: Accepted  
**Phase**: 30 – Distributed Query Engine, SQL Processing & Analytics Framework  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires an on-demand SQL query engine capable of parsing, optimizing, and evaluating SELECT query statements across active node catalogs without relying on external relational databases.

---

## Decision

We implement a complete **Distributed Query Engine, SQL Processing & Analytics Framework**:

1. **QueryCatalog**: Thread-safely indexes metadata configurations and schemas.
2. **QueryParser**: Tokenizes SELECT statements extracting ASTs.
3. **QueryPlanner**: Builds sequential scan and projection stages.
4. **QueryOptimizer**: Moves FILTER conditions after SCAN stages (predicate pushdown).
5. **QueryFunctionRegistry**: Houses built-in routines (e.g. UPPER/LOWER).
6. **AggregationEngine**: Evaluates aggregates values (e.g. COUNT/SUM/AVG).
7. **QueryExecutor**: Evaluates plans against datasets.
8. **QueryService**: Exposes query submit endpoints on the MessageBus.

---

## Consequences

- **Predicate Pushdowns**: Pushing down filters avoids scanning unnecessary elements.
- **Unified Function Registry**: Centralizes scalar functions registrations in a single place.
- **Strict Decoupling**: Plan builders are independent of socket loopbacks.
