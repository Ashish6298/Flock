"""ConsensusLog – ordered, integrity-checked replicated log for Raft.

The ``ConsensusLog`` maintains an ordered sequence of ``LogEntry`` records
with 1-based indexing that mirrors the Raft paper's convention.  It is the
authoritative source of truth for log state on any given node, whether that
node is currently a Follower, Candidate, or Leader.

Invariants enforced by this class:
* Log indices are contiguous and start at 1.
* The ``commit_index`` never decreases.
* Entries at or below ``commit_index`` are immutable and cannot be truncated.
* Appending entries that conflict with committed entries raises
  ``LogConflictError`` (a safety violation).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Tuple

from flock.consensus.exceptions import LogConflictError
from flock.consensus.models import LogEntry


class ConsensusLog:
    """Thread-safe, append-only (below commit point) replicated Raft log.

    Indices used throughout are **1-based** following the Raft paper.  The
    internal list stores entries at position ``entry.index - 1`` so that
    ``_entries[0]`` holds the entry at log index 1.

    Thread safety:
        All public methods acquire ``_lock`` internally.  Callers must not
        hold ``_lock`` themselves when calling public methods to avoid
        deadlocks.
    """

    def __init__(self) -> None:
        self._entries: List[LogEntry] = []
        self._commit_index: int = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def last_index(self) -> int:
        """Index of the last entry in the log, or 0 if the log is empty."""
        with self._lock:
            return len(self._entries)

    @property
    def last_term(self) -> int:
        """Term of the last entry in the log, or 0 if the log is empty."""
        with self._lock:
            if not self._entries:
                return 0
            return self._entries[-1].term

    @property
    def commit_index(self) -> int:
        """Highest log index known to be committed (never decreases)."""
        with self._lock:
            return self._commit_index

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_entry(self, index: int) -> Optional[LogEntry]:
        """Return the ``LogEntry`` at ``index``, or ``None`` if out of range.

        Args:
            index: 1-based log index.

        Returns:
            ``LogEntry`` at ``index`` or ``None``.
        """
        with self._lock:
            if index < 1 or index > len(self._entries):
                return None
            return self._entries[index - 1]

    def get_range(self, start: int, end: int) -> List[LogEntry]:
        """Return a slice of log entries from ``start`` to ``end`` inclusive.

        Args:
            start: 1-based start index (clamped to 1 if below).
            end:   1-based end index (clamped to last index if beyond).

        Returns:
            List of ``LogEntry`` objects (may be empty).
        """
        with self._lock:
            lo = max(start, 1) - 1          # convert to 0-based
            hi = min(end, len(self._entries))  # end is inclusive
            return list(self._entries[lo:hi])

    def has_entry(self, index: int, term: int) -> bool:
        """Return ``True`` if the log contains an entry with matching index and term.

        This is the consistency check used in AppendEntries processing:
        ``prev_log_index`` and ``prev_log_term`` must match for the
        follower to accept new entries.

        Args:
            index: 1-based log index (0 means "before the log", always True).
            term:  Expected term at ``index``.
        """
        if index == 0:
            return True  # vacuously consistent – no previous entry required
        with self._lock:
            if index > len(self._entries):
                return False
            return self._entries[index - 1].term == term

    def get_term_at(self, index: int) -> int:
        """Return the term of the entry at ``index``, or 0 if not present.

        Args:
            index: 1-based log index.
        """
        with self._lock:
            if index < 1 or index > len(self._entries):
                return 0
            return self._entries[index - 1].term

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def append(self, entries: List[LogEntry]) -> None:
        """Append a contiguous sequence of entries to the log.

        Each entry's index must be exactly one greater than the previous
        entry's index (or one greater than the current last index for the
        first entry in the list).  Entries must not overlap with or
        conflict with any committed entries.

        Args:
            entries: Ordered list of ``LogEntry`` objects to append.

        Raises:
            LogConflictError: If an entry's index is not contiguous or
                conflicts with a committed entry.
            ValueError: If ``entries`` is empty.
        """
        if not entries:
            return

        with self._lock:
            expected_index = len(self._entries) + 1
            for entry in entries:
                if entry.index != expected_index:
                    raise LogConflictError(
                        f"Non-contiguous log append: expected index {expected_index}, "
                        f"got {entry.index}"
                    )
                if entry.index <= self._commit_index:
                    raise LogConflictError(
                        f"Cannot overwrite committed log entry at index {entry.index} "
                        f"(commit_index={self._commit_index})"
                    )
                self._entries.append(entry)
                expected_index += 1

    def truncate_from(self, index: int) -> int:
        """Remove all entries at ``index`` and beyond.

        Used by followers to repair conflicting log tails before accepting
        entries from the leader.  Committed entries are never truncated.

        Args:
            index: 1-based index from which to truncate (inclusive).

        Returns:
            Number of entries removed.

        Raises:
            LogConflictError: If ``index`` falls within the committed range.
        """
        with self._lock:
            if index <= self._commit_index:
                raise LogConflictError(
                    f"Cannot truncate committed log entry at index {index} "
                    f"(commit_index={self._commit_index})"
                )
            if index > len(self._entries):
                return 0  # nothing to truncate
            removed = len(self._entries) - (index - 1)
            self._entries = self._entries[: index - 1]
            return removed

    def commit(self, index: int) -> None:
        """Advance the commit index to ``index`` if ``index`` is higher.

        The commit index never decreases.  If ``index`` exceeds the last log
        entry, it is clamped to ``last_index`` so the commit pointer is always
        within the bounds of the actual log.

        Args:
            index: New commit index (must be ≥ current commit_index).
        """
        with self._lock:
            clamped = min(index, len(self._entries))
            if clamped > self._commit_index:
                self._commit_index = clamped

    # ------------------------------------------------------------------
    # Snapshot support (Phase 13 hook)
    # ------------------------------------------------------------------

    def snapshot_state(self) -> Tuple[List[LogEntry], int]:
        """Return a copy of all committed entries and the commit index.

        This method is the integration point for Phase 13 – Persistent
        Distributed Log & Snapshot Management.  The returned data may be
        serialised to stable storage without risk of mutation.

        Returns:
            Tuple of (committed_entries, commit_index).
        """
        with self._lock:
            committed = list(self._entries[: self._commit_index])
            return committed, self._commit_index

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the total number of entries in the log."""
        with self._lock:
            return len(self._entries)

    def __repr__(self) -> str:
        return (
            f"ConsensusLog(size={len(self._entries)}, "
            f"commit_index={self._commit_index})"
        )
