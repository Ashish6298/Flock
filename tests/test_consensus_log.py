"""Unit tests for ConsensusLog – ordered replicated Raft log.

Tests cover:
* Empty log initialization
* Single and batch entry appends
* Index continuity validation (gap rejection)
* Commit index advancement (monotone)
* truncate_from removing conflicting suffix
* has_entry positive and negative cases
* get_range boundary cases
* snapshot_state correctness
* Attempt to truncate committed entries (safety guard)
"""

import pytest
from flock.consensus.log import ConsensusLog
from flock.consensus.models import LogEntry
from flock.consensus.exceptions import LogConflictError


def make_entry(index: int, term: int, command: bytes = b"cmd") -> LogEntry:
    return LogEntry(index=index, term=term, command=command)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_empty_log_initial_state() -> None:
    log = ConsensusLog()
    assert log.last_index == 0
    assert log.last_term == 0
    assert log.commit_index == 0
    assert len(log) == 0


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------

def test_append_single_entry() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    assert log.last_index == 1
    assert log.last_term == 1
    assert len(log) == 1


def test_append_multiple_entries() -> None:
    log = ConsensusLog()
    entries = [make_entry(i, 1) for i in range(1, 4)]
    log.append(entries)
    assert log.last_index == 3
    assert len(log) == 3


def test_append_empty_list_is_noop() -> None:
    log = ConsensusLog()
    log.append([])
    assert len(log) == 0


def test_append_non_contiguous_raises_conflict_error() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    with pytest.raises(LogConflictError):
        log.append([make_entry(3, 1)])  # index 3 skips 2


def test_append_duplicate_index_raises_conflict_error() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    with pytest.raises(LogConflictError):
        log.append([make_entry(1, 2)])  # duplicate


def test_append_below_commit_raises_conflict_error() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    log.commit(2)
    with pytest.raises(LogConflictError):
        log.append([make_entry(2, 2)])  # index 2 is committed


# ---------------------------------------------------------------------------
# Get entry and range
# ---------------------------------------------------------------------------

def test_get_entry_returns_correct_entry() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1, b"hello")])
    entry = log.get_entry(1)
    assert entry is not None
    assert entry.command == b"hello"
    assert entry.index == 1
    assert entry.term == 1


def test_get_entry_out_of_range_returns_none() -> None:
    log = ConsensusLog()
    assert log.get_entry(0) is None
    assert log.get_entry(1) is None


def test_get_range_full() -> None:
    log = ConsensusLog()
    log.append([make_entry(i, 1) for i in range(1, 6)])
    r = log.get_range(1, 5)
    assert len(r) == 5
    assert r[0].index == 1
    assert r[-1].index == 5


def test_get_range_partial() -> None:
    log = ConsensusLog()
    log.append([make_entry(i, 1) for i in range(1, 6)])
    r = log.get_range(2, 4)
    assert len(r) == 3
    assert r[0].index == 2
    assert r[-1].index == 4


def test_get_range_beyond_end_is_clamped() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    r = log.get_range(1, 100)
    assert len(r) == 1


# ---------------------------------------------------------------------------
# has_entry
# ---------------------------------------------------------------------------

def test_has_entry_zero_always_true() -> None:
    log = ConsensusLog()
    assert log.has_entry(0, 0) is True


def test_has_entry_matching() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 3)])
    assert log.has_entry(1, 3) is True


def test_has_entry_wrong_term() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 3)])
    assert log.has_entry(1, 5) is False


def test_has_entry_out_of_range() -> None:
    log = ConsensusLog()
    assert log.has_entry(5, 1) is False


# ---------------------------------------------------------------------------
# Commit index
# ---------------------------------------------------------------------------

def test_commit_advances_index() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    log.commit(2)
    assert log.commit_index == 2


def test_commit_never_decreases() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    log.commit(2)
    log.commit(1)  # should be ignored
    assert log.commit_index == 2


def test_commit_beyond_log_is_ignored() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    log.commit(99)  # clamped internally
    # commit only advances to len(entries)
    assert log.commit_index == 1


# ---------------------------------------------------------------------------
# Truncate
# ---------------------------------------------------------------------------

def test_truncate_removes_suffix() -> None:
    log = ConsensusLog()
    log.append([make_entry(i, 1) for i in range(1, 6)])
    removed = log.truncate_from(3)
    assert removed == 3
    assert log.last_index == 2


def test_truncate_beyond_log_is_noop() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    removed = log.truncate_from(99)
    assert removed == 0


def test_truncate_committed_entry_raises() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    log.commit(2)
    with pytest.raises(LogConflictError):
        log.truncate_from(1)


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

def test_snapshot_returns_committed_entries() -> None:
    log = ConsensusLog()
    log.append([make_entry(i, 1) for i in range(1, 4)])
    log.commit(2)
    entries, ci = log.snapshot_state()
    assert ci == 2
    assert len(entries) == 2
    assert entries[-1].index == 2


def test_snapshot_empty_if_nothing_committed() -> None:
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    entries, ci = log.snapshot_state()
    assert ci == 0
    assert entries == []


# ---------------------------------------------------------------------------
# LogEntry validation
# ---------------------------------------------------------------------------

def test_log_entry_index_must_be_positive() -> None:
    with pytest.raises(Exception):
        LogEntry(index=0, term=1)


def test_log_entry_term_must_be_non_negative() -> None:
    with pytest.raises(Exception):
        LogEntry(index=1, term=-1)
