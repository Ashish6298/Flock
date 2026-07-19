"""Typed exception hierarchy for the Flock Raft Consensus subsystem.

All exceptions in this module derive from a single base class,
``ConsensusError``, enabling callers to catch the entire family with
a single ``except`` clause while retaining the ability to discriminate
between specific failure modes.
"""

from flock.exceptions import FlockError


class ConsensusError(FlockError):
    """Base exception for all Raft consensus subsystem errors."""


class InvalidTermError(ConsensusError):
    """Raised when a message carries a term number that is stale or invalid.

    This exception is raised when an incoming Raft RPC contains a term that is
    less than the receiving node's current term, indicating a message from a
    deposed or partitioned leader/candidate.
    """


class LogConflictError(ConsensusError):
    """Raised when log index and term do not match the local log.

    Triggered during AppendEntries validation when the previous log index and
    term asserted by the leader do not correspond to the local log state,
    indicating a conflicting history that requires truncation or resync.
    """


class ElectionTimeoutError(ConsensusError):
    """Raised when an election timer expires without reaching quorum.

    A candidate that does not collect a majority of votes before its randomised
    election timeout fires will raise this exception to trigger a new election
    attempt with an incremented term.
    """


class LeaderUnavailableError(ConsensusError):
    """Raised when no leader is known for the current term.

    Callers attempting operations that require an active leader (e.g., log
    submission) receive this exception when the cluster has not yet elected a
    leader or the previous leader has been deposed.
    """


class ConsensusViolationError(ConsensusError):
    """Raised when a Raft safety property would be violated.

    This exception signals that an attempted state transition or operation
    would breach a fundamental Raft invariant, such as committing entries
    below the current commit index, electing a second leader in the same
    term, or advancing a term without proper vote accounting.
    """


class ReplicationFailureError(ConsensusError):
    """Raised when a log replication attempt is rejected by a follower.

    The leader raises this exception when a follower returns a negative
    AppendEntries response and the error cannot be reconciled through
    nextIndex back-tracking within the allowed retry budget.
    """


class QuorumNotReachedError(ConsensusError):
    """Raised when a quorum cannot be established.

    Used during vote tallying and commit index advancement when the number
    of affirmative responses is insufficient to satisfy the majority
    requirement ``(cluster_size // 2) + 1``.
    """
