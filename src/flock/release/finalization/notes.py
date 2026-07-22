"""Release notes and migration guides builders."""

from __future__ import annotations

import threading
from flock.release.finalization.models import BenchmarkSummary


class ReleaseNotesBuilder:
    """Compiles official release notes, performance summaries, and migration instructions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def compile_release_notes(self, version: str, benchmarks: BenchmarkSummary) -> str:
        """Produce release notes document text."""
        with self._lock:
            return f"""Flock v{version} General Availability Release Notes
==================================================

We are proud to announce the stable GA release of Flock!
Flock is a secure, federated, and AI-optimized distributed computing platform.

Performance Benchmarks Summary:
- Total Transactions Processed: {benchmarks.total_tx_processed}
- Average Latency: {benchmarks.avg_latency_ms} ms
- Consensus status: {benchmarks.raft_consensus_status}

Migration Guide:
- No breaking API changes from v0.38+.
- Core schemas and message ranges have been finalized.
"""
