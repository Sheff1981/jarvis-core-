"""Security Lab foundations: explicit scope, Tor research routing and audit decisions.

No network access or offensive action is performed by this module.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import ip_address
from urllib.parse import urlsplit
import json


@dataclass(frozen=True)
class Scope:
    hosts: tuple
    expires_at: str
    approved_by_owner: bool = False

    def permits(self, url):
        if not self.approved_by_owner:
            return False
        try:
            if datetime.fromisoformat(self.expires_at.replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                return False
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return False
            return parsed.hostname.lower() in self.hosts
        except (ValueError, TypeError):
            return False


class SecurityPolicy:
    RESEARCH = "research"
    LAB = "lab"
    PENTEST = "authorized_pentest"

    def __init__(self, scope=None):
        self.scope = scope

    def authorize(self, mode, target=None, *, lab_isolated=False):
        if mode == self.RESEARCH:
            return {"allowed": True, "reason": "Passive reading only; no target probing"}
        if mode == self.LAB:
            return {"allowed": bool(lab_isolated), "reason": "Isolated training environment required"}
        if mode == self.PENTEST:
            allowed = bool(target and self.scope and self.scope.permits(target))
            return {"allowed": allowed, "reason": "Owner-approved, unexpired exact-host scope required"}
        return {"allowed": False, "reason": "Unknown mode"}

    @staticmethod
    def research_route(url, *, tor_enabled=False):
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Invalid research URL")
        if parsed.username or parsed.password:
            raise ValueError("Credentials in URL prohibited")
        hostname = parsed.hostname.lower()
        if hostname.endswith(".onion"):
            if not tor_enabled or parsed.scheme != "http" and parsed.scheme != "https":
                raise ValueError("Onion research requires explicitly enabled Tor")
            return "tor"
        try:
            ip = ip_address(hostname)
            if not ip.is_global:
                raise ValueError("Private address research prohibited")
        except ValueError as error:
            if "Private address" in str(error):
                raise
        return "tor" if tor_enabled else "direct"

    @staticmethod
    def audit_record(mode, target, decision):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode, "target": target, "decision": decision
        }, ensure_ascii=False)
