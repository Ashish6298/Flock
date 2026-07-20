"""Load Balancing Heuristics."""

from __future__ import annotations

import abc
import random
from typing import List, Optional

from flock.resources.models import NodeResourceProfile


class LoadBalancingStrategy(abc.ABC):
    """Abstract interface defining required load balancing algorithms."""

    @abc.abstractmethod
    def select_node(self, nodes: List[NodeResourceProfile]) -> Optional[str]:
        """Choose a node from list of candidate resource profiles."""
        pass


class LeastUtilizedStrategy(LoadBalancingStrategy):
    """Chooses node possessing the lowest CPU utilization profile."""

    def select_node(self, nodes: List[NodeResourceProfile]) -> Optional[str]:
        if not nodes:
            return None
        # Sort nodes by cpu_util ascending
        sorted_nodes = sorted(nodes, key=lambda n: n.cpu_util)
        return sorted_nodes[0].node_id


class RoundRobinStrategy(LoadBalancingStrategy):
    """Simple round robin selector."""

    def __init__(self) -> None:
        self._index = 0

    def select_node(self, nodes: List[NodeResourceProfile]) -> Optional[str]:
        if not nodes:
            return None
        node_id = nodes[self._index % len(nodes)].node_id
        self._index += 1
        return node_id


class LoadBalancingEngine:
    """Invokes pluggable load balancing strategies to balance workloads."""

    def __init__(self, strategy: LoadBalancingStrategy) -> None:
        self.strategy = strategy

    def select_candidate(self, candidates: List[NodeResourceProfile]) -> Optional[str]:
        """Invoke active strategy selection query."""
        return self.strategy.select_node(candidates)
