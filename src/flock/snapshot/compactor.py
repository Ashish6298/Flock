"""Raft log compaction and truncation engine."""

from __future__ import annotations

import threading
import time
from typing import Optional

import structlog

from flock.consensus.log import ConsensusLog
from flock.snapshot.exceptions import SnapshotCompactionError
from flock.snapshot.models import CompactionStatistics

logger = structlog.get_logger()


class LogCompactor:
    """Safely truncates committed log prefixes while preserving safety bounds."""

    def __init__(self, consensus_log: ConsensusLog) -> None:
        self._log = consensus_log
        self._lock = threading.Lock()

    def compact(self, last_included_index: int, last_included_term: int) -> CompactionStatistics:
        """Safely discard prefix entries of consensus log up to last_included_index.

        Enforces:
        1. Compact index cannot exceed consensus commit index.
        2. Entries up to last_included_index must be safely discarded.

        Args:
            last_included_index: The index up to which log compaction happens.
            last_included_term: The term associated with the last_included_index.

        Returns:
            CompactionStatistics detailing the compaction execution results.
        """
        with self._lock:
            commit_index = self._log.commit_index
            if last_included_index > commit_index:
                raise SnapshotCompactionError(
                    f"Compaction index {last_included_index} exceeds commit index {commit_index}."
                )

            # Compact the log entries
            with self._log._lock:
                original_len = len(self._log._entries)
                
                # Filter out entries up to last_included_index
                truncated_entries = [e for e in self._log._entries if e.index > last_included_index]
                truncated_count = original_len - len(truncated_entries)

                self._log._entries = truncated_entries
                
                # Persist the snapshot boundary values inside log
                # We need some fields to allow consensus.log to know about truncated prefix term.
                # Let's add dynamic fields to ConsensusLog if needed, or simply assign them.
                # In Raft, the log gets annotated with last_included_index and last_included_term.
                setattr(self._log, "last_included_index", last_included_index)
                setattr(self._log, "last_included_term", last_included_term)

            logger.info(
                "Raft log compacted",
                last_included_index=last_included_index,
                last_included_term=last_included_term,
                entries_truncated=truncated_count,
            )

            return CompactionStatistics(
                last_included_index=last_included_index,
                last_included_term=last_included_term,
                entries_truncated=truncated_count,
                timestamp=time.time(),
            )
