# ADR 0022 – Distributed Scheduling, Cron Engine & Event-Driven Automation

**Date**: 2026-07-20  
**Status**: Accepted  
**Phase**: 22 – Distributed Scheduling, Cron Engine & Event-Driven Automation  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires a distributed scheduling engine capable of executing workflows periodically via cron expressions, intervals, or event triggers under authoritative leader ownership.

---

## Decision

We implement a complete **Distributed Scheduling, Cron Engine & Event-Driven Automation**:

1. **CronEngine**: Parses 5-field cron strings and calculates next run time increments.
2. **EventTriggerEngine**: Matches EventBus event notifications to registered scheduling triggers.
3. **ScheduleRegistry**: Thread-safe database tracking active scheduling definition blueprints.
4. **SchedulingEngine**: Dispatches execution events on timer intervals only if this node holds Raft scheduler leadership.
5. **SchedulingService**: Integrates scheduler synchronization routes on the message bus.

---

## Consequences

- **Exactly-Once Execution**: Leader-ownership semantics ensure scheduled tasks are not executed multiple times concurrently in the cluster.
- **Failover Protection**: Followers skip schedules, but automatically take over scheduling execution triggers upon acquiring Raft leadership.
- **Event-Driven Automation**: Dynamically starts workflows on custom EventBus patterns.
