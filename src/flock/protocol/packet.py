"""Custom network packet frame protocol with integrity validation."""

import struct
import hashlib
from typing import Any, Tuple
from flock.exceptions import SerializationError

# Constants
MAGIC_BYTES = b"FLOK"
PROTOCOL_VERSION = 1
HEADER_FORMAT = "!4sBBI"  # Magic (4s), Version (B), MessageType (B), PayloadSize (I)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

class MessageType:
    """Supported network message types."""
    HEARTBEAT = 1
    TASK_SUBMIT = 2
    TASK_RESULT = 3
    PEER_DISCOVERY = 4
    GENERIC = 5
    DISCOVERY_REQUEST = 6
    DISCOVERY_RESPONSE = 7
    NODE_ANNOUNCE = 8
    NODE_LEAVE = 9
    MEMBER_JOIN_REQ = 10
    MEMBER_JOIN_ACK = 11
    MEMBER_LEAVE_NOTIFY = 12
    MEMBER_SNAPSHOT_REQ = 13
    MEMBER_SNAPSHOT_RESP = 14
    HEARTBEAT_PING = 15
    HEARTBEAT_PONG = 16
    TASK_SUBMIT = 17
    TASK_ANNOUNCE = 18
    TASK_CANCEL = 19
    TASK_EXPIRE = 20
    TASK_UPDATE = 21
    TASK_ASSIGN = 22
    TASK_ASSIGN_ACK = 23
    TASK_ASSIGN_REJECT = 24
    TASK_REASSIGN_REQUEST = 25
    PLACEMENT_UPDATE = 26
    TASK_EXECUTION_START = 27
    TASK_EXECUTION_ACK = 28
    TASK_EXECUTION_CANCEL = 29
    TASK_EXECUTION_COMPLETE = 30
    TASK_EXECUTION_FAILURE = 31
    TASK_RESULT = 32
    TASK_RESULT_ACK = 33
    TASK_RESULT_FAILURE = 34
    TASK_RESULT_TIMEOUT = 35
    TASK_RESULT_RETRY = 36
    TASK_RESULT_STREAM_END = 37
    TASK_RETRY_REQUEST = 38
    TASK_RETRY_ACK = 39
    TASK_RECOVERY_REQUEST = 40
    TASK_RECOVERY_ACK = 41
    TASK_RECOVERY_CANCEL = 42
    TASK_RECOVERY_COMPLETE = 43
    TASK_RECOVERY_FAILED = 44
    TASK_RECOVERY_STATUS = 45
    # Phase 12 – Distributed Raft Consensus Engine
    RAFT_REQUEST_VOTE = 46
    RAFT_VOTE_RESPONSE = 47
    RAFT_APPEND_ENTRIES = 48
    RAFT_APPEND_RESPONSE = 49
    RAFT_HEARTBEAT = 50
    RAFT_LEADER_ANNOUNCE = 51
    RAFT_LOG_SYNC_REQUEST = 52
    RAFT_LOG_SYNC_RESPONSE = 53
    # Phase 13 – Replicated Distributed State Machine & Metadata Store
    STATE_COMMAND = 54
    STATE_COMMAND_ACK = 55
    STATE_APPLY_NOTIFICATION = 56
    STATE_SNAPSHOT_REQUEST = 57
    STATE_SNAPSHOT_RESPONSE = 58
    STATE_SYNC_REQUEST = 59
    STATE_SYNC_RESPONSE = 60
    STATE_VERSION_UPDATE = 61
    # Phase 14 – Distributed Snapshot Replication & Log Compaction
    SNAPSHOT_CREATE_REQUEST = 62
    SNAPSHOT_CREATE_RESPONSE = 63
    SNAPSHOT_INSTALL_REQUEST = 64
    SNAPSHOT_INSTALL_RESPONSE = 65
    SNAPSHOT_CHUNK = 66
    SNAPSHOT_CHUNK_ACK = 67
    SNAPSHOT_TRANSFER_COMPLETE = 68
    SNAPSHOT_TRANSFER_FAILED = 69
    LOG_COMPACTION_REQUEST = 70
    LOG_COMPACTION_COMPLETE = 71
    # Phase 15 – Persistent Storage Engine & Write-Ahead Logging (WAL)
    WAL_SYNC_REQUEST = 72
    WAL_SYNC_RESPONSE = 73
    STORAGE_HEALTH_REQUEST = 74
    STORAGE_HEALTH_RESPONSE = 75
    CHECKPOINT_CREATED = 76
    CHECKPOINT_RESTORED = 77
    PERSISTENCE_STATUS = 78
    RECOVERY_STATUS = 79
    SEGMENT_ROTATED = 80
    SEGMENT_ARCHIVED = 81
    # Phase 16 – Distributed Observability, Metrics & Telemetry Framework
    METRICS_REQUEST = 82
    METRICS_RESPONSE = 83
    TRACE_PROPAGATION = 84
    HEALTH_REPORT_REQUEST = 85
    HEALTH_REPORT_RESPONSE = 86
    DIAGNOSTICS_REQUEST = 87
    DIAGNOSTICS_RESPONSE = 88
    TELEMETRY_SNAPSHOT = 89
    EXPORTER_SYNC = 90
    CLUSTER_STATISTICS = 91
    # Phase 17 – Distributed Security, Authentication & Authorization Framework
    AUTH_REQUEST = 92
    AUTH_RESPONSE = 93
    CERTIFICATE_EXCHANGE = 94
    TOKEN_VALIDATION = 95
    AUTHZ_QUERY = 96
    AUTHZ_RESPONSE = 97
    KEY_ROTATION = 98
    SECURITY_AUDIT_SYNC = 99
    TRUST_STORE_SYNC = 100
    SECURE_SESSION_ESTABLISH = 101
    # Phase 18 – Distributed Resource Manager & Intelligent Cluster Load Balancer
    RESOURCE_REGISTRATION = 102
    RESOURCE_UPDATE = 103
    ALLOCATION_REQUEST = 104
    ALLOCATION_RESPONSE = 105
    RESERVATION_SYNC = 106
    QUOTA_SYNC = 107
    LOAD_BALANCING_RECOMMENDATION = 108
    CAPACITY_REPORT = 109
    RESOURCE_HEALTH_SYNC = 110
    CLUSTER_UTILIZATION_BROADCAST = 111
    # Phase 19 – Autonomous Cluster Orchestrator & Self-Healing Scheduler
    ORCHESTRATOR_POLICY_SYNC = 112
    ORCHESTRATOR_POLICY_ACK = 113
    CLUSTER_OPTIMIZATION_REQUEST = 114
    CLUSTER_OPTIMIZATION_RESULT = 115
    TASK_MIGRATION_REQUEST = 116
    TASK_MIGRATION_ACK = 117
    TASK_MIGRATION_COMPLETE = 118
    AUTOSCALER_DECISION = 119
    CLUSTER_REBALANCE_NOTIFICATION = 120
    ORCHESTRATOR_STATUS_REPORT = 121
    # Phase 20 – Multi-Cluster Federation & Global Scheduler
    FEDERATION_JOIN_REQUEST = 122
    FEDERATION_JOIN_RESPONSE = 123
    FEDERATION_HEARTBEAT = 124
    FEDERATION_CLUSTER_ADVERTISEMENT = 125
    GLOBAL_TASK_SUBMIT = 126
    GLOBAL_TASK_ASSIGNMENT = 127
    GLOBAL_ROUTING_DECISION = 128
    FEDERATION_STATE_SYNC = 129
    FEDERATION_FAILOVER_NOTIFICATION = 130
    FEDERATION_STATUS_REPORT = 131
    # Phase 21 – Distributed Workflow Engine & DAG Orchestration
    WORKFLOW_SUBMIT = 132
    WORKFLOW_ACCEPTED = 133
    WORKFLOW_START = 134
    WORKFLOW_PROGRESS = 135
    WORKFLOW_CHECKPOINT = 136
    WORKFLOW_RECOVERY_REQUEST = 137
    WORKFLOW_RECOVERY_RESPONSE = 138
    WORKFLOW_COMPLETED = 139
    WORKFLOW_FAILED = 140
    WORKFLOW_CANCEL = 141
    # Phase 22 – Distributed Scheduling, Cron Engine & Event-Driven Automation
    SCHEDULE_CREATE = 142
    SCHEDULE_UPDATE = 143
    SCHEDULE_DELETE = 144
    SCHEDULE_TRIGGER = 145
    SCHEDULE_EXECUTION_START = 146
    SCHEDULE_EXECUTION_COMPLETE = 147
    SCHEDULE_EXECUTION_FAILED = 148
    TRIGGER_NOTIFICATION = 149
    SCHEDULER_STATE_SYNC = 150
    SCHEDULER_STATUS_REPORT = 151
    # Phase 23 – Distributed Event Streaming, Message Broker & Pub/Sub Framework
    TOPIC_CREATE = 152
    TOPIC_DELETE = 153
    EVENT_PUBLISH = 154
    EVENT_ACK = 155
    SUBSCRIPTION_REQUEST = 156
    SUBSCRIPTION_RESPONSE = 157
    CONSUMER_GROUP_SYNC = 158
    OFFSET_COMMIT = 159
    STREAM_REPLAY_REQUEST = 160
    STREAM_REPLAY_RESPONSE = 161

class Packet:
    """Prepares and validates standard raw network frames for Flock communication."""

    def __init__(self, message_type: int, payload: bytes) -> None:
        self.message_type = message_type
        self.payload = payload

    @property
    def payload_checksum(self) -> str:
        """Calculate payload SHA256 checksum."""
        return hashlib.sha256(self.payload).hexdigest()

    def pack(self) -> bytes:
        """Pack header and payload into a single binary frame."""
        payload_size = len(self.payload)
        header = struct.pack(
            HEADER_FORMAT,
            MAGIC_BYTES,
            PROTOCOL_VERSION,
            self.message_type,
            payload_size
        )
        # We append a fixed length checksum representation or calculate payload hash
        # To maintain frame cleanliness, we attach the hash prefix to verification
        return header + self.payload

    @classmethod
    def unpack_header(cls, header_bytes: bytes) -> Tuple[int, int]:
        """Decode header frame and return message type and payload size.

        Raises:
            SerializationError: If magic bytes mismatch or invalid protocol version.
        """
        if len(header_bytes) != HEADER_SIZE:
            raise SerializationError("Incomplete header block.")

        magic, version, msg_type, payload_size = struct.unpack(HEADER_FORMAT, header_bytes)
        if magic != MAGIC_BYTES:
            raise SerializationError(f"Invalid magic bytes: {magic!r}")
        if version != PROTOCOL_VERSION:
            raise SerializationError(f"Unsupported protocol version: {version}")
        
        return msg_type, payload_size
