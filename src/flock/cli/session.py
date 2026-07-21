"""Session Manager tracking active token authorizations."""

from __future__ import annotations

import time
from typing import Dict

from flock.cli.exceptions import SessionExpiredError
from flock.cli.models import SessionMetadata


class SessionManager:
    """Validates login lifetimes."""

    def __init__(self) -> None:
        self.sessions: Dict[str, SessionMetadata] = {}

    def create_session(self, session_id: str, token: str, duration_sec: float) -> SessionMetadata:
        """Create new session record."""
        meta = SessionMetadata(
            session_id=session_id,
            token=token,
            expires_at=time.time() + duration_sec,
        )
        self.sessions[session_id] = meta
        return meta

    def validate_session(self, session_id: str) -> None:
        """Verify session is valid.

        Raises:
            SessionExpiredError: If token does not exist or has expired.
        """
        if session_id not in self.sessions:
            raise SessionExpiredError(f"Session '{session_id}' not found.")
        
        meta = self.sessions[session_id]
        if time.time() > meta.expires_at:
            raise SessionExpiredError(f"Session '{session_id}' has expired.")
