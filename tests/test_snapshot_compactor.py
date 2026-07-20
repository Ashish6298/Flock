"""Unit tests for LogCompactor."""

import pytest
from flock.consensus.log import ConsensusLog
from flock.consensus.models import LogEntry
from flock.snapshot.compactor import LogCompactor
from flock.snapshot.exceptions import SnapshotCompactionError


def make_entry(index: int, term: int) -> LogEntry:
    return LogEntry(index=index, term=term, command=b"cmd")


def test_log_compactor_truncates_log() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1), make_entry(3, 1)])
    log.commit(2)

    compactor = LogCompactor(log)
    stats = compactor.compact(last_included_index=2, last_included_term=1)

    assert stats.entries_truncated == 2
    assert len(log._entries) == 1
    assert log._entries[0].index == 3
    assert getattr(log, "last_included_index") == 2


def test_compaction_beyond_commit_raises() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    log.commit(1)  # only index 1 committed

    compactor = LogCompactor(log)
    with pytest.raises(SnapshotCompactionError):
        # Index 2 exceeds commit index 1
        compactor.compact(last_included_index=2, last_included_term=1)
