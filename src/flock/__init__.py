"""Flock framework core package initialization."""

from flock.exceptions import FlockError
from flock.types import NodeInfo, TaskSpec, TaskStatus

__version__ = "0.1.0"
__all__ = [
    "FlockError",
    "NodeInfo",
    "TaskSpec",
    "TaskStatus",
]
