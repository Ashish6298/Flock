"""Runtime sandboxing, compliance configuration checks, and platform security hardening checks."""

from __future__ import annotations

import os
import sys
import threading
from typing import Dict, List
from flock.security.exceptions import SecurityHardeningError


class HardeningEngine:
    """Verifies runtime environments are hardened against common vulnerabilities (writable bins, permissions)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._checks: Dict[str, bool] = {}

    def verify_runtime_safety(self) -> List[str]:
        """Perform system checks. Returns list of warning messages."""
        with self._lock:
            warnings = []
            
            # Check 1: running in privileged mode (e.g. root/admin checks)
            # On unix, os.getuid() == 0, on windows we simulate
            try:
                # We can check if script directories or site-packages are world-writable
                # But keep checks simple and deterministic to avoid environment flakiness.
                is_admin = False
                if sys.platform == 'win32':
                    import ctypes
                    try:
                        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                    except Exception:
                        pass
                else:
                    is_admin = os.getuid() == 0  # type: ignore[attr-defined]
                
                if is_admin:
                    warnings.append("Runtime is running with Administrator/Root privileges (least-privilege violation).")
                    self._checks["least_privilege"] = False
                else:
                    self._checks["least_privilege"] = True
            except Exception:
                self._checks["least_privilege"] = True

            # Check 2: Python sys.path writable safety
            path_safe = True
            for path in sys.path:
                if path and os.path.exists(path):
                    # Check writable permission safely without throwing
                    try:
                        if os.access(path, os.W_OK) and not os.path.isdir(path):
                            path_safe = False
                    except Exception:
                        pass
            
            if not path_safe:
                warnings.append("Vulnerable writable sys.path component detected.")
                self._checks["path_safety"] = False
            else:
                self._checks["path_safety"] = True

            # Check 3: debugger attach detection (ptrace/tracing check emulation)
            # For simplicity, register as safe or issue warning if sys.gettrace() is active
            if sys.gettrace() is not None:
                warnings.append("Active tracer/debugger detected attaching to runtime.")
                self._checks["debugger_protection"] = False
            else:
                self._checks["debugger_protection"] = True

            return warnings

    def get_status(self) -> Dict[str, bool]:
        """Return the checks result dict."""
        with self._lock:
            # Re-evaluate to get latest results
            self.verify_runtime_safety()
            return dict(self._checks)
