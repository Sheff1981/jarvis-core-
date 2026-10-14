"""Explicit, single-use authorization for local computer actions.

This module intentionally does not execute OS commands.
"""
from dataclasses import dataclass
import secrets
import threading


@dataclass(frozen=True)
class ActionRequest:
    token: str
    operation: str
    target: str
    description: str


class PermissionGate:
    """Deny by default; approvals are scoped to one exact action."""

    def __init__(self):
        self._lock = threading.Lock()
        self._pending = {}
        self._approved = {}

    def propose(self, operation, target, description):
        if not all(isinstance(v, str) and v.strip() for v in
                   (operation, target, description)):
            raise ValueError("Action fields must be nonempty strings")
        request = ActionRequest(
            secrets.token_urlsafe(24), operation.strip(),
            target.strip(), description.strip()
        )
        with self._lock:
            self._pending[request.token] = request
        return request

    def approve(self, token):
        with self._lock:
            request = self._pending.pop(token, None)
            if request is None:
                return False
            self._approved[token] = request
            return True

    def deny(self, token):
        with self._lock:
            return self._pending.pop(token, None) is not None

    def consume(self, token, operation, target):
        """Consume authorization once, even if requested scope mismatches."""
        with self._lock:
            request = self._approved.pop(token, None)
            return bool(request and request.operation == operation
                        and request.target == target)

    def revoke_all(self):
        with self._lock:
            self._pending.clear()
            self._approved.clear()
