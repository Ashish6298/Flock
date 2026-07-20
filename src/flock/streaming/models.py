"""Streaming Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Topic(BaseModel):
    """Represents a logic messaging stream topic."""
    topic_id: str
    name: str
    partitions_count: int = 1

    model_config = {
        "frozen": True
    }


class Partition(BaseModel):
    """Represents a single partition within a topic."""
    partition_id: int
    topic_id: str
    leader_node: str

    model_config = {
        "frozen": True
    }


class EventMessage(BaseModel):
    """Represents a single event payload inside a partition."""
    message_id: str
    topic_id: str
    partition_id: int
    payload: bytes
    offset: int
    timestamp: float

    model_config = {
        "frozen": True
    }


class ConsumerGroup(BaseModel):
    """Represents a consumer group balancing topic partitions."""
    group_id: str
    members: List[str] = Field(default_factory=list)
    topic_ids: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }


class ConsumerOffset(BaseModel):
    """Represents the current committed offset coordinate inside a partition."""
    group_id: str
    topic_id: str
    partition_id: int
    offset: int

    model_config = {
        "frozen": True
    }


class Subscription(BaseModel):
    """Represents an active publisher/subscriber subscription mapping."""
    subscription_id: str
    client_id: str
    topic_id: str

    model_config = {
        "frozen": True
    }


class StreamMetadata(BaseModel):
    """Overall metric summary for partitions storage details."""
    total_messages: int
    retention_bytes: int

    model_config = {
        "frozen": True
    }


class PublishRequest(BaseModel):
    """Represents a publisher publish demand payload."""
    topic_id: str
    payload: bytes
    key: Optional[str] = None

    model_config = {
        "frozen": True
    }


class DeliveryReceipt(BaseModel):
    """Represents the broker acknowledgement result sent to publisher."""
    message_id: str
    offset: int
    partition_id: int
    success: bool

    model_config = {
        "frozen": True
    }
