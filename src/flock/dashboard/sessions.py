"""Dashboard Session Manager.

Manages authenticated dashboard sessions including creation, validation,
expiry, and revocation.  Sessions are kept in an in-process store;
they can be extended to a distributed store by replacing the backing
dict with a :class:`~flock.datagrid` operation in production.
"""

import threading
import time
import uuid
from typing import Dict, List, Optional

from flock.dashboard.exceptions import SessionExpiredError
from flock.dashboard.models import SessionToken


class SessionManager:
    """Thread-safe in-process dashboard session manager.

    Sessions have a configurable time-to-live and are automatically
    considered expired when the current time exceeds ``expires_at``.

    Attributes:
        _lock: Reentrant lock protecting the session store.
        _sessions: Mapping of session_id to SessionToken.
        _ttl_seconds: Default session duration in seconds.
    """

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        """Initialise the session manager.

        Args:
            ttl_seconds: Default session TTL in seconds (default 1 hour).
        """
        self._lock: threading.RLock = threading.RLock()
        self._sessions: Dict[str, SessionToken] = {}
        self._ttl_seconds: float = ttl_seconds

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        username: str,
        roles: Optional[List[str]] = None,
        ttl_seconds: Optional[float] = None,
    ) -> SessionToken:
        """Create and store a new authenticated session.

        Args:
            username: Identity of the authenticated user.
            roles: Optional list of roles granted to the session.
            ttl_seconds: Override TTL for this session.

        Returns:
            The newly created :class:`SessionToken`.
        """
        session_id = str(uuid.uuid4())
        expires_at = time.time() + (ttl_seconds or self._ttl_seconds)
        token = SessionToken(
            session_id=session_id,
            username=username,
            roles=roles or [],
            expires_at=expires_at,
        )
        with self._lock:
            self._sessions[session_id] = token
        return token

    def revoke(self, session_id: str) -> None:
        """Revoke a session immediately.

        Args:
            session_id: Identifier of the session to revoke.
        """
        with self._lock:
            self._sessions.pop(session_id, None)

    def revoke_all_for_user(self, username: str) -> int:
        """Revoke all sessions belonging to a user.

        Args:
            username: Username whose sessions should be revoked.

        Returns:
            The number of sessions revoked.
        """
        with self._lock:
            to_remove = [
                sid for sid, tok in self._sessions.items()
                if tok.username == username
            ]
            for sid in to_remove:
                del self._sessions[sid]
        return len(to_remove)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, session_id: str) -> SessionToken:
        """Validate that a session is active and not expired.

        Args:
            session_id: Identifier of the session to validate.

        Returns:
            The valid :class:`SessionToken`.

        Raises:
            SessionExpiredError: If the session does not exist or has
                expired.
        """
        with self._lock:
            token = self._sessions.get(session_id)

        if token is None or time.time() > token.expires_at:
            raise SessionExpiredError(
                f"Session '{session_id}' is invalid or has expired."
            )
        return token

    def is_valid(self, session_id: str) -> bool:
        """Return ``True`` if the session exists and has not expired."""
        try:
            self.validate(session_id)
            return True
        except SessionExpiredError:
            return False

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get(self, session_id: str) -> Optional[SessionToken]:
        """Return a session token or ``None`` if not found / expired."""
        with self._lock:
            token = self._sessions.get(session_id)
        if token is None or time.time() > token.expires_at:
            return None
        return token

    def list_active(self) -> List[SessionToken]:
        """Return all non-expired session tokens."""
        now = time.time()
        with self._lock:
            return [t for t in self._sessions.values() if now <= t.expires_at]

    def count_active(self) -> int:
        """Return the number of currently active sessions."""
        return len(self.list_active())

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def purge_expired(self) -> int:
        """Remove all expired sessions from the store.

        Returns:
            The number of sessions removed.
        """
        now = time.time()
        with self._lock:
            expired = [
                sid for sid, tok in self._sessions.items()
                if now > tok.expires_at
            ]
            for sid in expired:
                del self._sessions[sid]
        return len(expired)

    def clear(self) -> None:
        """Remove all sessions (active and expired)."""
        with self._lock:
            self._sessions.clear()
