<div align="center">


# 🐦 Flock &nbsp;•&nbsp; A Distributed Computing Framework for Python

<br>

<table>
<tr>
<td align="center">

[![PyPI](https://img.shields.io/pypi/v/flock-p2p.svg?style=for-the-badge&color=3776AB&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/flock-p2p/)

</td>
<td align="center">

[![Python](https://img.shields.io/pypi/pyversions/flock-p2p.svg?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/flock-p2p/)

</td>
<td align="center">

[![Downloads](https://static.pepy.tech/badge/flock-p2p?style=for-the-badge)](https://pepy.tech/project/flock-p2p)

</td>
</tr>
<tr>
<td align="center">

[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</td>
<td align="center">

[![CI](https://img.shields.io/github/actions/workflow/status/Ashish6298/Flock/ci.yml?style=for-the-badge&label=CI&logo=githubactions&logoColor=white)](https://github.com/Ashish6298/Flock/actions)

</td>
<td align="center">

[![Tests](https://img.shields.io/badge/tests-629%20passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](#testing)

</td>
</tr>
</table>

[**Get Started**](#installation) &nbsp;•&nbsp; [Quick Start](#quick-start) &nbsp;•&nbsp; [Architecture](#architecture) &nbsp;•&nbsp; [API Reference](#api-reference) &nbsp;•&nbsp; [Contributing](#contributing)

</div>

<br>

## Overview

Flock is a fully-typed Python framework for building systems that run across multiple machines. It bundles the components a distributed system normally needs — Raft consensus, leader election, cluster membership, a message bus, scheduling, and security — into one importable package, so you wire up services with dependency injection instead of standing up separate infrastructure.

It's built around 42 focused subsystems (`flock.consensus`, `flock.scheduler`, `flock.security`, `flock.workflow`, and others), each independently testable and typed under `mypy --strict`.

| | |
|---|---|
| **Language** | Python 3.11+ |
| **Core dependency footprint** | `pydantic`, `structlog`, `msgpack` |
| **Consensus model** | Raft (leader election, log replication, snapshots) |
| **Transport** | Pluggable — TCP built in |
| **Install** | `pip install flock-p2p` |

<br>


## Table of Contents
<table width="1000">
<tr>
<td width="330" valign="top">

<b>🚀 Getting Started</b>

- [Overview](#overview)
- [Why Flock](#why-flock)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)

</td>

<td width="340" valign="top">

<b>🏗️ Reference</b>

- [Architecture](#architecture)
- [Subsystems](#subsystems)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Examples](#examples)

</td>

<td width="330" valign="top">

<b>📦 Project</b>

- [Testing](#testing)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)
- [Citation](#citation)

</td>
</tr>
</table>

<br>

## The Story Behind Flock

<div align="center">

### 💡 A single computer is no longer enough.

</div>

Whether it's traffic outgrowing one server, data too big for one machine, or uptime that can't depend on a single point of failure — the fix is always the same: run your software across **multiple computers working together as one.**

That's **distributed computing**. It quietly powers Netflix, Google, WhatsApp, and Uber. But here's what most tutorials leave out:

> ### "Building a distributed system from scratch is one of the hardest things in software engineering."

<br>

<table width="100%">
<tr>
<td align="center" width="20%">

**🩹**
**Fault Tolerance**

<sub>What happens when a server crashes mid-op?</sub>

</td>
<td align="center" width="20%">

**👑**
**Leader Election**

<sub>Who's in charge, with no single source of truth?</sub>

</td>
<td align="center" width="20%">

**🔄**
**Consistency**

<sub>How do 5 machines agree on the same data?</sub>

</td>
<td align="center" width="20%">

**🔒**
**Security**

<sub>How do you stop traffic interception?</sub>

</td>
<td align="center" width="20%">

**📊**
**Observability**

<sub>How do you catch failures before users do?</sub>

</td>
</tr>
</table>

<br>

These problems have occupied computer scientists for decades. Google and Amazon threw years of engineering effort at solving them internally — most teams don't have that runway.

**That's why Flock exists** — one `pip install` for infrastructure that used to take enterprise teams years to build.

<details>
<summary><b>📖 Read the full story</b></summary>
<br>

Flock was born from a simple frustration: developers shouldn't have to spend months building infrastructure before they can start building their actual product — especially when the Python ecosystem had no single, cohesive package that solved this.

The tools that solve consensus, replication, security, and observability have always existed — but scattered across research papers, expensive enterprise platforms, or locked inside the infrastructure teams of large tech companies. Nothing brought them together for the average Python developer.

Flock closes that gap: open-source, fully typed, and built to give any developer the same caliber of distributed-systems infrastructure that used to be exclusive to the biggest engineering teams in the world.

</details>

<br>

## What Problem Does Flock Solve?

Flock provides a **complete distributed systems stack** in Python — mapping familiar real-world problems to concrete solutions:

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

<details>
<summary><b>🍳 Prefer an analogy? The Restaurant Kitchen Problem</b></summary>
<br>

Imagine running a restaurant. On a quiet Tuesday, one chef handles everything. On a Friday night with 200 customers, that one chef becomes a bottleneck — you need **multiple chefs working together**, which raises new problems:

- **Who's the head chef**, and who takes over if they go home sick? → *leader election*
- **A chef drops a dish mid-prep** — who picks it up where it was left off? → *fault tolerance*
- **How do two chefs avoid cooking the same order twice?** → *consensus*
- **How do you stop the dishwasher from accessing the safe?** → *security & RBAC*
- **How do you know which chef is overloaded, in real time?** → *observability*

Flock solves all of these — not for kitchens, but for any system that needs to run across multiple servers.

</details>

<br>

## Who Is Flock For?

Flock scales from a student reading source code for the first time to an enterprise team running hundreds of clusters.

<table width="100%">
<tr>
<td align="center" width="18%">🎓 Students & Learners</td>
<td align="center" width="23%">👨‍💻 Developers & Side Projects</td>
<td align="center" width="21%">🏢 Startups & Small Teams</td>
<td align="center" width="15%">🏭 Enterprise</td>
<td align="center" width="25%">🔬 Researchers & Data Scientists</td>
</tr>
</table>

<br>

<details>
<summary><b>🎓 Students & Learners</b></summary>
<br>

See a *real*, working implementation of Raft consensus, leader election, distributed state machines, and service meshes — not just theory. Every subsystem is documented, strictly typed, and built to textbook standards, so the source code doubles as a reference implementation.

```bash
pip install flock-p2p
python -c "from flock.consensus import ConsensusService; help(ConsensusService)"
```

</details>

<details>
<summary><b>👨‍💻 Individual Developers & Side Projects</b></summary>
<br>

Skip weeks of reading consensus papers and debugging race conditions — install Flock and have a working distributed foundation in an afternoon.

**Use cases:** personal projects outgrowing a single VPS · home lab clusters (Raspberry Pi farms) · distributed data pipelines · multiplayer game server backends · distributed web scrapers

</details>

<details>
<summary><b>🏢 Startups & Small Engineering Teams</b></summary>
<br>

A team of 2–5 engineers doesn't need to become distributed-systems experts to run production infrastructure. Consensus, replication, security, and observability are already solved.

**Use cases:** multi-region SaaS deployment · distributed task queues with guaranteed execution · real-time multi-node data processing · highly available APIs with automatic failover

</details>

<details>
<summary><b>🏭 Enterprise & Large Organizations</b></summary>
<br>

Built-in support for multi-cloud federation, policy-as-code governance, compliance auditing, fleet management, RBAC, secrets vaulting, and intrusion detection — capabilities most companies otherwise build in-house over years.

**Use cases:** multi-cloud infrastructure across AWS/GCP/Azure · compliance auditing (HIPAA, SOC2) · fleet management across hundreds of nodes · disaster recovery with point-in-time restore · policy-enforced workload governance

</details>

<details>
<summary><b>🔬 Researchers & Data Scientists</b></summary>
<br>

Distribute an ML training job across multiple GPUs or machines, or build a data pipeline that processes terabytes of data — Flock provides the distributed execution substrate so you can focus on the algorithm, not the infrastructure.

</details>

<br>

## How Does Flock Help You?

### The Traditional Approach (Without Flock)

Building the same distributed foundation from scratch typically looks like this:

| Timeline | What You're Building | The Hard Part |
|---|---|---|
| **Month 1–2** | A consensus algorithm (Raft or Paxos) | Debugging election edge cases, split-brain scenarios |
| **Month 3** | A membership registry | Heartbeats, node join/leave, network partitions |
| **Month 4** | A message bus | Protocol design, serialization, versioning, backward compatibility |
| **Month 5–6** | Security | TLS, authentication, authorization, secrets management |
| **Month 7–8** | Observability | Metrics collection, distributed tracing, alerting |
| **Month 9+** | *Finally* — your actual product | — |

<div align="center">

**⏱️ ~9 months before writing a single line of business logic — for a skilled team.**

</div>

<br>

## The Flock Approach

```bash
pip install flock-p2p   # 30 seconds
```

```python
# A few minutes to a working distributed system
from flock.consensus import ConsensusService
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus

consensus = ConsensusService("node-1", membership, message_bus, event_bus)
await consensus.start()

# You now have Raft consensus, leader election, log replication,
# fault tolerance, and event publishing. Start building your product.
```

<div align="center">

**⏱️ Time to a working distributed foundation: under an hour.**

</div>

<br>

### The Difference, By the Numbers

| Metric | Build Yourself | With Flock |
|---|---|---|
| Time to first working cluster | Months | Minutes |
| Infrastructure code you maintain | Thousands of lines | Already written |
| Test coverage for edge cases | You write it all | 629 tests included |
| Consensus algorithm correctness | Your responsibility | Implemented Raft, unit-tested |
| Security posture | Your responsibility | Built-in mTLS, RBAC, secrets vault |
| Ongoing maintenance | On you | Shared with the OSS community |

<br>

## ✨ Features

<div align="left">

### **CORE PLATFORM**

</div>
<div align="center">
</tr></table>
</div>
<br>
<table width="100%">
<tr>
<td align="center" width="20%">

### ⚡ **Full Raft Consensus**

<sub>Leader election, log replication, state machine, term management, log compaction</sub>

</td>
<td align="center" width="20%">

### 🌐 **Cluster Membership**

<sub>Node discovery, heartbeat health monitoring, live membership registry</sub>

</td>
<td align="center" width="20%">

### 🔄 **Distributed State Machine**

<sub>Consistent replicated state with snapshotting and WAL</sub>

</td>
<td align="center" width="20%">

### 📡 **Transport-Independent Messaging**

<sub>Pluggable transport (TCP built-in); typed message routing</sub>

</td>
<td align="center" width="20%">

### 🗂️ **DataGrid**

<sub>In-memory distributed KV store — replication, partitioning, failover</sub>

</td>
</tr>
</table>

<br>

<div align="left">

### **EXECUTION & SCHEDULING**

</div>
<br>
<table width="100%">
<tr>
<td align="center" width="25%">

### 🧠 **AI-Powered Orchestration**

<sub>ML-based placement, predictive autoscaling, anomaly detection</sub>

</td>
<td align="center" width="25%">

### 📋 **Workflow Engine**

<sub>DAG workflows with checkpointing, parallelism, failure recovery</sub>

</td>
<td align="center" width="25%">

### ⏰ **Advanced Scheduler**

<sub>Cron, event-driven, deadline-aware scheduling</sub>

</td>
<td align="center" width="25%">

### 🎯 **Constraint-Aware Placement**

<sub>CPU/memory/affinity/anti-affinity placement engine</sub>

</td>
</tr>
</table>

<br>

<div align="left">

### **ENTERPRISE INFRASTRUCTURE**

</div>
<br>
<table width="100%">
<tr>
<td align="center" width="33%">

### 🔒 **Zero-Trust Security**

<sub>mTLS, RBAC, certificate management, credential rotation, intrusion detection</sub>

</td>
<td align="center" width="33%">

### 🛡️ **Secrets Vault**

<sub>Encrypted storage, key rotation, compliance auditing</sub>

</td>
<td align="center" width="33%">

### 📊 **Full Observability**

<sub>Tracing, structured logging, metrics, alerts, profiling, dashboards</sub>

</td>
</tr>
<tr>
<td align="center" width="33%">

### 🌍 **Multi-Cloud Federation**

<sub>Cross-region federation, latency-aware routing, trust handshakes</sub>

</td>
<td align="center" width="33%">

### 🏛️ **Control Plane**

<sub>Fleet management, cluster enrollment, org governance</sub>

</td>
<td align="center" width="33%">

### 📜 **Policy-as-Code**

<sub>Declarative policy compiler, rule engine, compliance enforcement</sub>

</td>
</tr>
<tr>
<td align="center" width="33%">

### 💾 **Disaster Recovery**

<sub>Automated snapshots, incremental backups, PITR restore</sub>

</td>
<td align="center" width="33%">

### 🛒 **Plugin Marketplace**

<sub>Package registry, dependency resolution, sandboxed execution</sub>

</td>
<td align="center" width="33%">

### 🚀 **Deployment Automation**

<sub>Docker/K8s manifests, rolling updates, rollback</sub>

</td>
</tr>
</table>

<br>

<div align="left">

### **DEVELOPER EXPERIENCE**

</div>

<table width="100%">
<tr>
<td align="center" width="25%">

### ✅ **629 Tests**

<sub>Full regression coverage, 42 subsystems</sub>

</td>
<td align="center" width="25%">

### 🔤 **Fully Typed**

<sub>`mypy --strict` clean, 390 source files</sub>

</td>
<td align="center" width="25%">

### 📦 **Single Install**

<sub>`pip install flock-p2p`</sub>

</td>
<td align="center" width="25%">

### 🐍 **Python 3.11+**

<sub>Modern Python, no legacy baggage</sub>

</td>
</tr>
</table>

<br>

## 📦 Installation

<div align="left">

```bash
pip install flock-p2p
```

</div>

### Requirements

| Dependency | Version | Purpose |
|---|---|---|
| **Python** | ≥ 3.11 | Runtime |
| `pydantic` | ≥ 2.0.0 | Data validation and models |
| `structlog` | ≥ 23.1.0 | Structured logging |
| `msgpack` | ≥ 1.0.0 | Binary serialization |

<br>

### Development Installation

For contributing or running the test suite locally:

**1. Clone the repository**
```bash
git clone https://github.com/Ashish6298/Flock.git
```

**2. Enter the project directory**
```bash
cd Flock
```

**3. Install in editable mode with dev dependencies**
```bash
pip install -e .[dev]
```

<sub>Dev extras include: `pytest` · `pytest-asyncio` · `mypy` · `black` · `ruff`</sub>

<br>

## 🚀 Quick Start  &nbsp;•&nbsp;  **Three examples. Each one runnable in under a minute.**

<table width="100%">
<tr>
<td align="center" width="33%">

### **🧱 Start a Cluster**
<sub>Raft consensus, leader election</sub>
</td>
<td align="center" width="33%">

### **🏛️ Join the Control Plane**
<sub>Fleet enrollment & governance</sub>
</td>
<td align="center" width="33%">

### **📋 Submit a Workflow**
<sub>DAG-based task execution</sub>
</td>
</tr>
</table>


---


### 1️⃣ Start a Single-Node Cluster

<sub>Spin up Raft consensus, elect a leader, and commit your first log entry.</sub>

<details open>
<summary><b>Show code</b></summary>
<br>

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

</details>

<br>

### 2️⃣ Register a Cluster with the Control Plane

<sub>Enroll a cluster into a fleet with labels, versioning, and active feature tracking.</sub>

<details>
<summary><b>Show code</b></summary>
<br>

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

</details>

<br>

### 3️⃣ Submit a Distributed Workflow

<sub>Define a DAG with dependencies and submit it for checkpointed execution.</sub>

<details>
<summary><b>Show code</b></summary>
<br>

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

</details>

<br>


## 🏗️ Architecture

Flock is a distributed, event-driven platform built around a strong consistency core.
The architecture connects application interfaces, coordination services, cluster nodes,
and persistence layers through a unified event graph.

<p align="center">
  <img src="./docs/assets/flock-architecture.svg" width="1000" alt="Flock Architecture"/>
</p>
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
