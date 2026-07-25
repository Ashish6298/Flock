"""Flock framework core package initialization."""

from importlib.metadata import version, PackageNotFoundError
from flock.exceptions import FlockError
from flock.types import NodeInfo, TaskSpec, TaskStatus

try:
    __version__ = version("flock-p2p")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "FlockError",
    "NodeInfo",
    "TaskSpec",
    "TaskStatus",
]
