"""Flock Consensus package – Distributed Raft Consensus Engine.

This package provides a complete, transport-independent implementation of the
Raft consensus algorithm for the Flock distributed task execution framework.
It establishes cluster-wide agreement on leader identity and log ordering
without depending on any networking implementation.

Primary entry point: ConsensusService
"""

from flock.consensus.service import ConsensusService

__all__ = ["ConsensusService"]
