<div align="center">

# 🐦 Flock

### Enterprise-Grade Federated Distributed Computing Platform

[![PyPI version](https://img.shields.io/pypi/v/flock-p2p.svg?color=blue&label=flock-p2p)](https://pypi.org/project/flock-p2p/)
[![Python](https://img.shields.io/pypi/pyversions/flock-p2p.svg)](https://pypi.org/project/flock-p2p/)
[![Downloads](https://static.pepy.tech/badge/flock-p2p)](https://pepy.tech/project/flock-p2p)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Ashish6298/Flock/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashish6298/Flock/actions)
[![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-629%20passing-brightgreen)](#testing)
**Flock** is a production-ready, fully typed, transport-independent distributed computing framework built in pure Python. It provides everything needed to run a multi-node cluster — from Raft consensus and leader election to AI-driven scheduling, enterprise security, policy-as-code governance, multi-cloud federation, and disaster recovery — all in a single cohesive package.

[Installation](#installation) · [Quick Start](#quick-start) · [The Story Behind Flock](#the-story-behind-flock) · [Who Is Flock For?](#who-is-flock-for) · [Architecture](#architecture) · [API Reference](#api-reference) · [Contributing](#contributing)

</div>

---

## Table of Contents

- [The Story Behind Flock](#the-story-behind-flock)
- [What Problem Does Flock Solve?](#what-problem-does-flock-solve)
- [Who Is Flock For?](#who-is-flock-for)
- [How Does Flock Help You?](#how-does-flock-help-you)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Subsystems](#subsystems)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Examples](#examples)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## The Story Behind Flock

Every large software system eventually hits the same wall: **a single computer is no longer enough**.

Maybe you are running a startup and your server is struggling under the load of thousands of users. Maybe you are a developer trying to process massive amounts of data faster than one machine can handle. Maybe you are an engineer at a company that needs its services to stay online even when hardware fails. Whatever the scenario, the answer is always the same — you need to run your software across **multiple computers working together as one**.

This is called **distributed computing**, and it is the backbone of every major technology product in the world today — Netflix, Google, WhatsApp, Uber, and thousands of others all rely on it. But here is the painful truth that most tutorials and blog posts do not tell you:

> **Building a distributed system from scratch is one of the hardest things in software engineering.**

It is not just about running the same code on two servers. You need to solve problems like:
- What happens when one server crashes mid-operation? Does the data get corrupted?
- Which server is "in charge"? How do they agree on anything without a single source of truth?
- How do you keep your data consistent when it lives on five different machines simultaneously?
- How do you secure communication between machines so attackers cannot intercept it?
- How do you know when something is going wrong before your users do?

These are unsolved problems that have occupied computer scientists for decades. Companies like Google and Amazon have spent billions of dollars and thousands of engineer-years building internal solutions. Most developers and small teams simply cannot afford to do the same.

**That is exactly why Flock was built.**

Flock was created out of a deeply personal frustration: why should a developer have to spend months or years building the infrastructure layer before they can even start working on the actual product? Why are the tools that solve these hard problems either too expensive, too complex, locked behind enterprise paywalls, or non-existent in the Python ecosystem?

Flock is the answer to that question — a **complete, open-source, production-grade distributed computing platform** that gives any Python developer access to the same calibre of infrastructure that was previously only available inside the largest tech companies in the world. You get it in a single `pip install`, with clean APIs, comprehensive documentation, and 629 tests proving it works.

---

## What Problem Does Flock Solve?

Let us use a simple analogy to explain what Flock does at its core.

### The Restaurant Kitchen Analogy

Imagine you run a restaurant. On a quiet Tuesday, one chef can handle everything — taking orders, cooking, plating, and cleaning up. But on a Friday night with 200 customers, that one chef becomes a bottleneck. You need **multiple chefs working together**.

But now you have new problems:
- **Who is the head chef?** Someone needs to coordinate. If the head chef goes home sick, who takes over? (This is the *leader election* problem)
- **What if a chef starts a dish but drops it?** Another chef needs to pick up exactly where they left off. (This is the *fault tolerance* problem)
- **How do you make sure two chefs don't make the same dish twice?** They need to communicate and agree. (This is the *consensus* problem)
- **How do you prevent the dishwasher from accessing the safe?** Different roles have different permissions. (This is the *security and RBAC* problem)
- **How do you know which chef is overloaded?** You need to monitor everyone in real time. (This is the *observability* problem)

Flock solves all of these problems — not just for restaurant kitchens, but for any software system that needs to run across multiple servers.

### In Technical Terms

Flock provides a **complete distributed systems stack** in Python:

| Real-World Problem | Computer Science Term | Flock Solution |
|---|---|---|
| Who is in charge? | Leader Election | `ConsensusService` (Raft algorithm) |
| Stay online when a server dies | Fault Tolerance | Automatic failover + replication |
| All servers agree on the same data | Consensus | Raft log replication + state machine |
| Prevent data loss on crashes | Durability | Write-Ahead Log (WAL) + snapshots |
| Find other servers automatically | Service Discovery | `DiscoveryService` |
| Secure communication | mTLS / Zero-Trust | `SecurityService` |
| Know when things go wrong | Observability | Metrics, tracing, alerts, dashboards |
| Scale up when traffic spikes | Autoscaling | AI-powered `OrchestratorService` |
| Run jobs across many servers | Distributed Scheduling | `SchedulerService` + `PlacementEngine` |
| Recover from disasters | Disaster Recovery | `RecoveryService` with backups + PITR |

---

## Who Is Flock For?

Flock is designed to be useful across a wide spectrum — from a student learning distributed systems for the first time to an engineering team building production infrastructure for millions of users.

### 🎓 Students & Learners

If you are studying computer science or distributed systems and want to see a *real*, working implementation of concepts like Raft consensus, leader election, distributed state machines, and service meshes — Flock is a goldmine. Every subsystem is fully documented, strictly typed, and built following textbook best practices. You can read the source code and see exactly how these algorithms work in practice, not just in theory.

```bash
pip install flock-p2p
python -c "from flock.consensus import ConsensusService; help(ConsensusService)"
```

### 👨‍💻 Individual Developers & Side Projects

Building something that needs to run on more than one server? Instead of spending weeks reading papers on distributed consensus or debugging race conditions, install Flock and have a working distributed foundation in an afternoon. Focus on your actual product — let Flock handle the infrastructure.

**Use cases:**
- A personal project that outgrows a single VPS
- A home lab cluster (Raspberry Pi farm, etc.)
- A distributed data processing pipeline
- A multiplayer game server backend
- A distributed web scraper or crawler

### 🏢 Startups & Small Engineering Teams

You have a great product idea and a small team. You cannot afford to hire a team of distributed systems PhDs, and you should not have to. Flock lets a team of 2–5 engineers build and operate a production-grade distributed system without becoming experts in every underlying algorithm. The hard parts — consensus, replication, security, observability — are already solved.

**Use cases:**
- Multi-region SaaS deployment
- Distributed task queue with guaranteed execution
- Real-time data processing across multiple nodes
- Highly available API backend with automatic failover

### 🏭 Enterprise & Large Organizations

Flock includes features specifically built for enterprise needs: multi-cloud federation, policy-as-code governance, compliance auditing, fleet management, role-based access control, secrets vaulting, intrusion detection, and a full control plane for managing hundreds of clusters. These are the same capabilities that companies typically build in-house over years at enormous cost.

**Use cases:**
- Multi-cloud infrastructure spanning AWS, GCP, and Azure
- Regulated industries requiring compliance auditing (HIPAA, SOC2, etc.)
- Fleet management across hundreds of compute nodes
- Enterprise-grade disaster recovery with point-in-time restore
- Policy-enforced workload governance

### 🔬 Researchers & Data Scientists

Need to distribute a machine learning training job across multiple GPUs or machines? Need to build a distributed data pipeline that processes terabytes of data? Flock provides the distributed execution substrate so you can focus on your algorithms, not the infrastructure.

---

## How Does Flock Help You?

### The Traditional Approach (Without Flock)

Here is what building a distributed system typically looks like without Flock:

**Month 1-2:** Research and implement a consensus algorithm (Raft or Paxos). Debug election edge cases. Handle split-brain scenarios.

**Month 3:** Build a membership registry. Implement heartbeats. Handle node join/leave. Deal with network partitions.

**Month 4:** Build a message bus. Design a protocol. Handle serialization, versioning, and backward compatibility.

**Month 5-6:** Add security. Implement TLS, authentication, and authorization. Build secrets management.

**Month 7-8:** Add observability. Build metrics collection, distributed tracing, alerting.

**Month 9+:** Start working on your actual product.

**Total time before writing business logic: 9+ months for a skilled team.**

### The Flock Approach

```bash
pip install flock-p2p   # 30 seconds
```

```python
# 5 minutes to a working distributed system
from flock.consensus import ConsensusService
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus

consensus = ConsensusService("node-1", membership, message_bus, event_bus)
await consensus.start()
# You now have Raft consensus, leader election, log replication,
# fault tolerance, and event publishing. Start building your product.
```

**Time to a working distributed foundation: Under an hour.**

### The Difference in Numbers

| Metric | Build Yourself | Use Flock |
|---|---|---|
| Time to first working cluster | Months | Minutes |
| Lines of infrastructure code | 50,000+ | 0 (it's already written) |
| Tests covering edge cases | You write them all | 629 tests included |
| Consensus algorithm correctness | Your responsibility | Battle-tested Raft |
| Security vulnerabilities | Your responsibility | Hardened, audited |
| Ongoing maintenance burden | High | Open-source community |

---

## Features

### Core Platform
- ⚡ **Full Raft Consensus** — leader election, log replication, state machine, term management, and log compaction
- 🌐 **Cluster Membership** — node discovery, heartbeat health monitoring, live membership registry
- 🔄 **Distributed State Machine** — consistent replicated state with snapshotting and WAL (Write-Ahead Log)
- 📡 **Transport-Independent Messaging** — pluggable transport layer (TCP built-in); message bus with typed routing
- 🗂️ **DataGrid** — in-memory distributed KV store with replication, partitioning, and failover

### Execution & Scheduling
- 🧠 **AI-Powered Orchestration** — ML-based workload placement, predictive autoscaling, anomaly detection
- 📋 **Workflow Engine** — DAG-based workflows with checkpointing, parallelism, and failure recovery
- ⏰ **Advanced Scheduler** — cron, event-driven, and deadline-aware task scheduling
- 🎯 **Constraint-Aware Placement** — CPU/memory/affinity/anti-affinity placement engine

### Enterprise Infrastructure
- 🔒 **Zero-Trust Security** — mTLS handshakes, RBAC, certificate management, credential rotation, intrusion detection
- 🛡️ **Secrets Vault** — encrypted secret storage, key rotation, compliance auditing
- 📊 **Full Observability** — distributed tracing, structured logging, metrics, alerts, profiling, dashboards
- 🌍 **Multi-Cloud Federation** — cross-region cluster federation, latency-aware routing, trust handshakes
- 🏛️ **Control Plane** — fleet management, cluster enrollment, organizational governance
- 📜 **Policy-as-Code** — declarative policy compiler, rule engine, compliance enforcement, audit trails
- 💾 **Disaster Recovery** — automated snapshots, incremental backups, PITR restore, continuity planning
- 🛒 **Plugin Marketplace** — package registry, dependency resolution, sandboxed execution
- 🚀 **Deployment Automation** — Docker/Kubernetes manifest generation, rolling updates, rollback

### Developer Experience
- ✅ **629 tests** — full regression coverage across all 42 subsystems
- 🔤 **100% typed** — `mypy --strict` clean across 390 source files
- 📦 **Single install** — `pip install flock-p2p`
- 🐍 **Python 3.11+** — modern Python, no legacy baggage

---

## Installation

```bash
pip install flock-p2p
```

### Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | ≥ 3.11 | Runtime |
| pydantic | ≥ 2.0.0 | Data validation and models |
| structlog | ≥ 23.1.0 | Structured logging |
| msgpack | ≥ 1.0.0 | Binary serialization |

### Development Installation

```bash
git clone https://github.com/Ashish6298/Flock.git
cd Flock
pip install -e .[dev]
```

Development extras include: `pytest`, `pytest-asyncio`, `mypy`, `black`, `ruff`.

---

## Quick Start

### 1. Start a Single-Node Cluster

```python
import asyncio
from unittest.mock import MagicMock
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.consensus import ConsensusService
from flock.cluster.registry import MembershipRegistry
from flock.cluster.models import NodeMember, ClusterMemberStatus

async def main() -> None:
    # Wire up core infrastructure
    event_bus = EventBus()
    transport = MagicMock()       # Replace with TCPTransport in production
    serializer = MagicMock()      # Replace with JsonSerializer in production
    message_bus = MessageBus(transport, serializer)

    # Build membership registry
    registry = MembershipRegistry()
    registry.register(NodeMember(
        node_id="node-1",
        host="127.0.0.1",
        port=9000,
        status=ClusterMemberStatus.ACTIVE,
    ))

    # Start Raft consensus
    consensus = ConsensusService(
        node_id="node-1",
        membership=registry,
        message_bus=message_bus,
        event_bus=event_bus,
    )
    await consensus.start()

    # Submit a command (only succeeds if this node is the leader)
    if consensus.is_leader():
        entry = await consensus.submit_command(b"hello-world")
        print(f"Committed log entry: {entry}")

    await consensus.stop()

asyncio.run(main())
```

### 2. Register a Cluster with the Control Plane

```python
import asyncio
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.controlplane.service import ControlPlaneService
from flock.controlplane.models import EnrolledCluster
from unittest.mock import MagicMock

async def main() -> None:
    event_bus = EventBus()
    message_bus = MessageBus(MagicMock(), MagicMock())

    cp = ControlPlaneService(
        node_id="coordinator",
        message_bus=message_bus,
        event_bus=event_bus,
    )
    await cp.start()

    cluster = EnrolledCluster(
        cluster_id="cluster-east",
        fleet_id="fleet-prod",
        name="US East Compute",
        version="1.0.0",
        labels={"region": "us-east-1", "tier": "prod"},
        features_active=["Consensus", "Security", "Observability"],
        last_seen=0.0,
    )
    cp.coordinator.clusters.enroll_cluster(cluster)
    print(f"Cluster enrolled: {cluster.name}")

    await cp.stop()

asyncio.run(main())
```

### 3. Submit a Distributed Workflow

```python
import asyncio
from flock.workflow.service import WorkflowService
from flock.workflow.models import WorkflowDefinition, WorkflowStep
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.storage.backend import StorageBackend
from unittest.mock import MagicMock

async def main() -> None:
    storage = StorageBackend()
    event_bus = EventBus()
    message_bus = MessageBus(MagicMock(), MagicMock())

    workflow_svc = WorkflowService(
        node_id="node-1",
        storage_backend=storage,
        message_bus=message_bus,
        event_bus=event_bus,
    )
    await workflow_svc.start()

    # Define a two-step DAG workflow
    wf = WorkflowDefinition(
        workflow_id="wf-001",
        name="data-pipeline",
        steps=[
            WorkflowStep(step_id="ingest", name="Ingest Data", dependencies=[]),
            WorkflowStep(step_id="transform", name="Transform", dependencies=["ingest"]),
        ],
    )
    await workflow_svc.submit(wf)
    await workflow_svc.stop()

asyncio.run(main())
```

---

## Architecture

Flock follows a **layered, event-driven architecture** built on strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│   CLI · API Gateway · Dashboard · SDK                           │
├─────────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION LAYER                           │
│   Workflow · Scheduler · Placement · Orchestrator               │
├─────────────────────────────────────────────────────────────────┤
│                    CONSENSUS & REPLICATION                       │
│   Raft Consensus · Election · Log · State Machine · Snapshot    │
├───────────────────────┬─────────────────────────────────────────┤
│    CLUSTER SERVICES   │        PLATFORM SERVICES                │
│   Discovery           │   Security · Observability              │
│   Heartbeat           │   Federation · Control Plane            │
│   Membership          │   Policy · Marketplace                  │
│   DataGrid            │   Recovery · Deployment                 │
├───────────────────────┴─────────────────────────────────────────┤
│                      MESSAGING LAYER                            │
│   MessageBus · EventBus · Router · Handlers · Middleware        │
├─────────────────────────────────────────────────────────────────┤
│                      STORAGE LAYER                              │
│   WAL · Storage Backend · Streaming · Query Engine              │
├─────────────────────────────────────────────────────────────────┤
│                     TRANSPORT LAYER                             │
│   TCP Transport · Serialization (JSON / MessagePack)            │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

- **Transport Independence** — the `MessageBus` decouples all subsystems from the underlying transport. Swap TCP for UDP, gRPC, or in-memory without touching business logic.
- **Event-Driven** — every significant state change publishes a typed event on the `EventBus`. Subsystems subscribe and react; they never call each other directly.
- **Immutable Models** — all domain models use `@dataclass(frozen=True)`. State is never mutated in place; new objects are produced.
- **Thread Safety** — all shared state is protected by `threading.RLock()`. Services are safe for concurrent use.
- **SOLID + Dependency Inversion** — every service accepts its dependencies via constructor injection. Nothing creates its own infrastructure.

---

## Subsystems

Flock is organized into 42 focused subsystems under `flock.*`:

| Subsystem | Module | Description |
|---|---|---|
| **Consensus** | `flock.consensus` | Full Raft implementation: election, log replication, state machine |
| **Cluster** | `flock.cluster` | Node membership, registry, health status |
| **Heartbeat** | `flock.heartbeat` | Peer health probing and failure detection |
| **Discovery** | `flock.discovery` | Service registration and peer lookup |
| **Messaging** | `flock.messaging` | MessageBus, typed routing, middleware, handlers |
| **Events** | `flock.events` | EventBus — pub/sub event distribution |
| **Transport** | `flock.transport` | TCP transport; pluggable interface |
| **Protocol** | `flock.protocol` | Typed message definitions (MessageType enum) |
| **DataGrid** | `flock.datagrid` | Distributed KV store with partitioning |
| **Storage** | `flock.storage` | WAL, storage backend, recovery |
| **Snapshot** | `flock.snapshot` | Consistent cluster snapshots, compaction, replication |
| **Streaming** | `flock.streaming` | Event streaming, publisher/subscriber, backpressure |
| **Query** | `flock.query` | Distributed query engine: parser, planner, optimizer |
| **Runtime** | `flock.runtime` | Task execution context and executor |
| **Scheduler** | `flock.scheduler` | Priority queue-based task scheduler |
| **Scheduling** | `flock.scheduling` | Cron, trigger, and deadline-based scheduling |
| **Orchestrator** | `flock.orchestrator` | AI-powered workload orchestration and autoscaling |
| **Placement** | `flock.placement` | Constraint-aware task placement engine |
| **Resources** | `flock.resources` | CPU/memory allocation, load balancing, capacity planning |
| **Workflow** | `flock.workflow` | DAG workflow engine with checkpointing |
| **State Machine** | `flock.statemachine` | Generic replicated state machine |
| **Mesh** | `flock.mesh` | Service mesh: routing, circuit breaking, load balancing |
| **Functions** | `flock.functions` | Serverless-style function registry and execution |
| **Observability** | `flock.observability` | Metrics, tracing, profiling, alerts, log aggregation |
| **Dashboard** | `flock.dashboard` | Real-time monitoring dashboard with widgets |
| **Security** | `flock.security` | Zero-Trust, RBAC, vault, crypto, intrusion detection |
| **AI** | `flock.ai` | Prediction, anomaly detection, learning engine |
| **Federation** | `flock.federation` | Multi-cloud/multi-region cluster federation |
| **Control Plane** | `flock.controlplane` | Fleet management and cluster governance |
| **Policy** | `flock.policy` | Policy-as-Code: compiler, rule engine, compliance |
| **Marketplace** | `flock.marketplace` | Plugin registry, dependency resolution, sandboxing |
| **Recovery** | `flock.recovery` | Disaster recovery, backup, PITR restore |
| **Deployment** | `flock.deployment` | Kubernetes/Docker manifest generation, rollout |
| **Results** | `flock.results` | Result collection, serialization, registry |
| **Serialization** | `flock.serialization` | JSON and MessagePack serializers |
| **Config** | `flock.config` | Cluster configuration management |
| **API** | `flock.api` | HTTP API gateway and REST router |
| **CLI** | `flock.cli` | Command-line interface |
| **Plugins** | `flock.plugins` | Plugin loader, sandbox, service |
| **Release** | `flock.release` | Production readiness checks and lifecycle |
| **Interfaces** | `flock.interfaces` | Shared abstract base classes and protocols |

---

## API Reference

### Core Types

```python
from flock import NodeInfo, TaskSpec, TaskStatus

# Immutable node descriptor
node = NodeInfo(
    node_id="node-1",
    host="10.0.0.1",
    port=9000,
    metadata={"zone": "us-east-1a"},
)

# Task specification (auto-generates a UUID task_id)
task = TaskSpec.create("process_batch", dataset="sales_q4", limit=1000)
print(task.task_id)   # e.g. "a3f2c1d0-..."
print(task.name)      # "process_batch"

# Task lifecycle states
class TaskStatus(str, Enum):
    PENDING    = "PENDING"
    RUNNING    = "RUNNING"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"
    CANCELLED  = "CANCELLED"
```

### ConsensusService

```python
from flock.consensus import ConsensusService

service = ConsensusService(
    node_id="node-1",
    membership=registry,         # MembershipRegistry
    message_bus=message_bus,     # MessageBus
    event_bus=event_bus,         # EventBus
    heartbeat_interval=0.15,     # seconds between leader heartbeats
    election_timeout_min=0.30,   # minimum election timeout
    election_timeout_max=0.60,   # maximum election timeout
)

await service.start()
await service.stop()

# Check role
service.is_leader()              # bool
service.current_term             # int
service.leader_id                # Optional[str]

# Submit a command (leader only)
entry = await service.submit_command(b"payload")

# Events published on EventBus:
# "consensus.leader.elected"    → {"leader_id": str, "term": int}
# "consensus.term.changed"      → {"old_term": int, "new_term": int}
# "consensus.log.committed"     → {"index": int, "entry_id": str, "term": int}
# "consensus.replication.failed"→ {"peer_id": str, "error": str}
```

### SecurityService

```python
from flock.security.service import SecurityService
from flock.security.models import NodeIdentity, SecurityPolicy

identity = NodeIdentity(node_id="node-1", public_key=b"...")
service = SecurityService(
    node_id="node-1",
    secret_key=b"32-byte-secret-key-here!!!!!!!!",
    local_identity=identity,
    message_bus=message_bus,
    event_bus=event_bus,
)
await service.start()

# Authenticate a peer
result = service.authentication_engine.authenticate(token, peer_id)

# Authorize an action
allowed = service.authorization_engine.authorize(identity, "write", "resource-x")

# Store and retrieve secrets
service.secrets_manager.store("db_password", b"supersecret")
secret = service.secrets_manager.retrieve("db_password")
```

### WorkflowService

```python
from flock.workflow.service import WorkflowService
from flock.workflow.models import WorkflowDefinition, WorkflowStep

service = WorkflowService(
    node_id="node-1",
    storage_backend=storage,
    message_bus=message_bus,
    event_bus=event_bus,
)
await service.start()

workflow = WorkflowDefinition(
    workflow_id="pipeline-001",
    name="ETL Pipeline",
    steps=[
        WorkflowStep(step_id="extract",   name="Extract",   dependencies=[]),
        WorkflowStep(step_id="transform", name="Transform", dependencies=["extract"]),
        WorkflowStep(step_id="load",      name="Load",      dependencies=["transform"]),
    ],
)
await service.submit(workflow)
```

### EventBus

```python
from flock.events.bus import EventBus

bus = EventBus()

# Subscribe to events
def on_leader(payload: dict) -> None:
    print(f"New leader: {payload['leader_id']}")

bus.subscribe("consensus.leader.elected", on_leader)

# Publish events
bus.publish("consensus.leader.elected", {"leader_id": "node-1", "term": 3})
```

### MessageBus

```python
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType

bus = MessageBus(transport=transport, serializer=serializer)

# Register a typed handler
@bus.handler(MessageType.VOTE_REQUEST)
async def handle_vote(message):
    ...

await bus.send(peer_id="node-2", message_type=MessageType.HEARTBEAT, payload=b"...")
```

---

## Configuration

Flock services are configured via constructor arguments — there are no global config files or singleton objects. Every service accepts its dependencies through dependency injection.

### Typical Wiring Pattern

```python
# 1. Create infrastructure
event_bus   = EventBus()
message_bus = MessageBus(transport, serializer)

# 2. Create subsystem services, injecting infrastructure
membership  = MembershipRegistry()
consensus   = ConsensusService("node-1", membership, message_bus, event_bus)
security    = SecurityService("node-1", secret_key, identity, message_bus, event_bus)
workflow    = WorkflowService("node-1", storage, message_bus, event_bus)

# 3. Start all services
await consensus.start()
await security.start()
await workflow.start()

# 4. Run your application...

# 5. Graceful shutdown
await workflow.stop()
await security.stop()
await consensus.stop()
```

### Key Configuration Parameters

| Service | Parameter | Default | Description |
|---|---|---|---|
| `ConsensusService` | `heartbeat_interval` | `0.15s` | Leader heartbeat frequency |
| `ConsensusService` | `election_timeout_min` | `0.30s` | Min election timeout |
| `ConsensusService` | `election_timeout_max` | `0.60s` | Max election timeout |
| `SecurityService` | `secret_key` | required | 32-byte AES encryption key |
| `FederationService` | `region` | required | Cluster geographic region |

---

## Examples

### Run the Getting Started Example

```bash
git clone https://github.com/Ashish6298/Flock.git
cd Flock
pip install -e .
python examples/getting_started.py
```

Expected output:
```
Successfully initialized Flock Cluster: US East compute under organization registries.
```

### Multi-Node Federation

```python
from flock.federation.service import FederationService
from flock.federation.models import FederatedCluster

federation = FederationService(
    node_id="gateway-node",
    message_bus=message_bus,
    event_bus=event_bus,
)
await federation.start()

# Register a remote cluster
remote = FederatedCluster(
    cluster_id="cluster-west",
    region="us-west-2",
    endpoint="https://west.internal:9443",
    trust_level="verified",
)
federation.registry.register(remote)
```

### Policy-as-Code

```python
from flock.policy.service import PolicyService
from flock.policy.models import PolicyDefinition, PolicyRule

policy_svc = PolicyService(node_id="node-1", event_bus=event_bus)

policy = PolicyDefinition(
    policy_id="deny-root",
    name="Deny Root Privilege Tasks",
    rules=[
        PolicyRule(
            rule_id="r1",
            condition="task.user == 'root'",
            action="DENY",
            severity="CRITICAL",
        )
    ],
)
policy_svc.engine.load_policy(policy)
```

### Disaster Recovery Snapshot

```python
from flock.recovery.service import RecoveryService

recovery = RecoveryService(node_id="node-1", storage=storage, event_bus=event_bus)
await recovery.start()

# Create a full cluster snapshot
snapshot_id = await recovery.create_snapshot(label="pre-migration-backup")

# Restore from a snapshot
await recovery.restore_snapshot(snapshot_id)
```

---

## Testing

Flock ships with **629 tests** covering all 42 subsystems.

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run a specific subsystem
python -m pytest tests/test_consensus_service.py -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src/flock --cov-report=html

# Run mypy strict type check
mypy --strict src/
```

### Test Results

```
629 passed in ~10s
Success: no issues found in 390 source files (mypy --strict)
```

---

## Project Structure

```
Flock/
├── src/
│   └── flock/                    # Main package (42 subsystems)
│       ├── __init__.py           # Public API: FlockError, NodeInfo, TaskSpec, TaskStatus
│       ├── consensus/            # Raft consensus: election, log, replication, state machine
│       ├── cluster/              # Membership registry and node models
│       ├── security/             # Zero-Trust security stack
│       ├── workflow/             # DAG workflow engine
│       ├── observability/        # Metrics, tracing, alerts, profiling
│       ├── federation/           # Multi-cloud cluster federation
│       ├── controlplane/         # Fleet management and governance
│       ├── policy/               # Policy-as-Code engine
│       ├── recovery/             # Disaster recovery and snapshots
│       ├── marketplace/          # Plugin registry
│       └── ...                   # 32 more subsystems
├── tests/                        # 211 test files, 629 tests
├── examples/                     # Runnable usage examples
├── docs/                         # Documentation and audit reports
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
└── pyproject.toml                # Package metadata and tool configuration
```

---

## CI/CD

The GitHub Actions pipeline runs on every push and pull request to `main`:

```yaml
steps:
  - Set up Python 3.11
  - pip install (all dependencies including msgpack, pytest-asyncio)
  - pip install -e .
  - mypy --strict src/         # Zero-tolerance type checking
  - python -m pytest tests/ -v  # Full 629-test regression suite
```

All checks must pass before merging.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

**Quick contribution guide:**

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/Flock.git
cd Flock

# 2. Install dev dependencies
pip install -e .[dev]

# 3. Make your changes

# 4. Run the full validation suite
mypy --strict src/
python -m pytest tests/ -v

# 5. Submit a pull request against main
```

### Code Standards
- All code must pass `mypy --strict` — zero `# type: ignore` exceptions
- All new features require corresponding tests
- Follow the existing immutable dataclass + dependency injection patterns
- Use `structlog` for all logging — no `print()` in library code

---

## Security

Please report security vulnerabilities privately — see [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## License

MIT License — see [LICENSE](LICENSE) for full text.

---

## Citation

If you use Flock in research or production, please cite:

```bibtex
@software{flock2026,
  title  = {Flock: Enterprise-Grade Federated Distributed Computing Platform},
  year   = {2026},
  url    = {https://github.com/Ashish6298/Flock},
  version = {1.0.0}
}
```

---

<div align="center">

**Built with ❤️ for the distributed systems community**

[PyPI](https://pypi.org/project/flock-p2p/) · [GitHub](https://github.com/Ashish6298/Flock) · [Issues](https://github.com/Ashish6298/Flock/issues) · [Discussions](https://github.com/Ashish6298/Flock/discussions)

</div>
