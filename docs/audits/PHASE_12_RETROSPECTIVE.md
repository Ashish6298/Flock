# PHASE 12 RETROSPECTIVE – Distributed Raft Consensus Engine

**Phase**: 12  
**Date**: 2026-07-20  
**Team**: Flock Engineering  

---

## Summary

Phase 12 implemented the complete Raft consensus algorithm for Flock across
seven clean, well-isolated modules. The phase delivered 98 automated tests
with a 100% pass rate, strict mypy compliance, and zero regressions against
the 40 previously completed tests.

---

## What Went Well

### 1. Clean Module Decomposition
Decomposing Raft into `log.py`, `state_machine.py`, `election.py`,
`replication.py`, and `service.py` made each component independently testable
and produced a very high test-to-code ratio. No module needed to understand
the internals of another.

### 2. Pydantic Frozen Models for Safety
Using Pydantic `frozen=True` models for all protocol RPCs (VoteRequest,
VoteResponse, AppendEntriesRequest, AppendEntriesResponse) prevented accidental
mutation of in-flight messages and made state transitions fully traceable.

### 3. No Real Timers in Tests
Setting `min_timeout_sec=9999, max_timeout_sec=9999` in all test-side
`ElectionEngine` instances completely eliminated timing-dependent flakiness
while allowing the actual timer code path to be exercised via direct
`trigger_election()` calls and `_election_timer_coro(0.0)` invocations.

### 4. Optimised Conflict Hint
Implementing the Raft paper's conflict index/term optimisation from the start
avoided the O(n) one-step back-tracking approach in production while keeping
the follower receiver implementation clean and well-tested.

---

## Challenges and Solutions

### 1. Python `bool(empty_object)` Pitfall
**Problem**: `ConsensusLog.__len__` returns 0 for an empty log, making
`bool(ConsensusLog()) == False`. Test helper functions using `log or ConsensusLog()`
silently created new instances instead of using the passed-in empty log,
causing tests to assert on the wrong object.

**Solution**: Changed all helper guards from `log or ConsensusLog()` to
`log if log is not None else ConsensusLog()`. Added a note to team documentation
about the falsy-container pitfall with custom `__len__` classes.

### 2. Self-Inclusion in Commit Index Calculation
**Problem**: When passing all peer node IDs (including the leader itself) to
`_advance_commit`, the leader's entry in `match_indexes` was initialised to 0
(since `_match_index` only tracks followers), effectively adding a phantom vote
at index 0 and diluting the quorum calculation.

**Solution**: The `_advance_commit` method now explicitly excludes `self.node_id`
from the `match_indexes` dict before calling `calculate_commit_index`, so the
leader's contribution is always counted through `self_index` parameter only.

### 3. Single-Node Auto-Promotion in Tests
**Problem**: `ElectionEngine.request_votes()` auto-promotes to leader immediately
when there are no peers (correct single-node behaviour). Several tests that
expected a CANDIDATE state after `trigger_election()` failed because no peers
were configured.

**Solution**: Tests that require CANDIDATE state added `.set_peers([...])` calls
with at least two peers before triggering elections.

---

## Lessons Learned

1. **Verify object identity before asserting side effects** in tests where the
   fixture setup and code under test share Python's mutable objects.
2. **Never use `or` to provide defaults for objects that implement `__len__`**
   unless the intent is truly "use this if truthy". Prefer explicit `is not None`.
3. **Raft's single-node behaviour is a first-class feature**, not an edge case.
   Auto-promoting to leader with zero peers is correct and should be tested
   explicitly alongside the multi-node path.
4. **Additive protocol extensions are cheap**: The 8 new MessageType constants
   required zero changes to existing serialisation infrastructure.

---

## Code Statistics

| Metric | Value |
|---|---|
| Production modules added | 7 (`consensus/`) |
| Production lines added | ~1,150 |
| Test files added | 5 |
| Test lines added | ~850 |
| Protocol constants added | 8 |
| Tests passing | 98/98 (100%) |
| Regressions | 0 |
| mypy errors | 0 |

---

## Next Phase

**Phase 13 – Persistent Distributed Log & Snapshot Management**

Key objectives for Phase 13:
- Persist `current_term`, `voted_for`, and log entries to stable storage before
  responding to any Raft RPC (Raft durability guarantee).
- Implement log compaction by replacing committed log prefixes with snapshots.
- Implement `InstallSnapshot` RPC for lagging followers.
- Define the `SnapshotStore` interface for pluggable storage backends.
