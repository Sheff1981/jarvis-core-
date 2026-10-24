"""Owner authorization and hard limits for autonomous JARVIS evolution.

Voice recognition is not authentication. Local code changes require an
owner-held random token and cannot modify this policy or its tests.
"""
import hashlib
import hmac
import os
from pathlib import Path


PROTECTED = frozenset({
    "jarvis/owner_policy.py",
    "jarvis/self_improvement.py",
    "tests/test_owner_policy.py",
    "tests/test_self_improvement.py",
    "jarvis_launcher.py",
})


class OwnerPolicy:
    def __init__(self, token_hash):
        if not isinstance(token_hash, str) or len(token_hash) != 64:
            raise ValueError("Owner token hash must be SHA-256 hex")
        self.token_hash = token_hash

    @classmethod
    def from_environment(cls):
        digest = os.environ.get("JARVIS_OWNER_TOKEN_SHA256", "")
        return cls(digest)

    def authorize(self, token):
        if not isinstance(token, str) or not token:
            return False
        return hmac.compare_digest(
            hashlib.sha256(token.encode("utf-8")).hexdigest(), self.token_hash)

    def require(self, token):
        if not self.authorize(token):
            raise PermissionError("Owner authorization required")

    def check_change(self, relative_path, token):
        self.require(token)
        if not isinstance(relative_path, str):
            raise ValueError("Invalid path")
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts or path.as_posix() in PROTECTED:
            raise PermissionError("Protected file cannot be self-modified")
        if not path.parts or path.parts[0] not in ("jarvis", "tests"):
            raise PermissionError("Changes must stay inside the code sandbox")
        return True
