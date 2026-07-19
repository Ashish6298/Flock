"""Queue abstractions sorting tasks by scheduling policy."""

import heapq
from typing import List, Optional, Tuple, cast
from flock.scheduler.models import Task, SchedulingPolicy
from flock.scheduler.exceptions import QueueCapacityError

class SchedulingQueue:
    """Asyncio-safe queue backing FIFO or priority ordering rules."""

    def __init__(self, policy: SchedulingPolicy = SchedulingPolicy.FIFO, max_size: int = 1000) -> None:
        self.policy = policy
        self.max_size = max_size
        self._fifo_list: List[Task] = []
        self._priority_heap: List[Tuple[int, int, Task]] = []
        self._counter = 0

    def push(self, task: Task) -> None:
        """Enqueue task.

        Raises:
            QueueCapacityError: If maximum capacity limit reached.
        """
        if len(self._fifo_list) + len(self._priority_heap) >= self.max_size:
            raise QueueCapacityError("Scheduling queue capacity limit reached")

        if self.policy == SchedulingPolicy.FIFO:
            self._fifo_list.append(task)
        else:
            # Min-heap prioritizes lowest numbers, but we want IntEnum CRITICAL (3) first.
            # Invert priority values so critical (3) maps to -3 and sorts first.
            priority_val = -int(task.metadata.priority)
            # Use counter to keep ordering stable on priority match
            self._counter += 1
            heapq.heappush(self._priority_heap, (priority_val, self._counter, task))

    def pop(self) -> Optional[Task]:
        """Pop next task according to policy."""
        if self.policy == SchedulingPolicy.FIFO:
            if self._fifo_list:
                return self._fifo_list.pop(0)
            return None
        else:
            if self._priority_heap:
                popped = heapq.heappop(self._priority_heap)
                return popped[2]
            return None

    def size(self) -> int:
        """Return total queue size."""
        return len(self._fifo_list) + len(self._priority_heap)
