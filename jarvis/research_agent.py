"""Read-only research pipeline with source review and explicit network boundaries.

Tor is a transport setting, not authorization to probe targets. This module
does not execute page instructions, scripts, downloads or fetched code.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler
from urllib.error import HTTPError
import ipaddress
import socket

from jarvis.security_lab import SecurityPolicy


@dataclass(frozen=True)
class ResearchResult:
    url: str
    route: str
    status: str
    bytes_read: int


class ResearchAgent:
    def __init__(self, academy, *, tor_enabled=False, transport=None):
        self.academy = academy
        self.tor_enabled = tor_enabled
        self.transport = transport

    @staticmethod
    def validate_public_url(url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Public research requires HTTPS without credentials")
        if parsed.port not in (None, 443):
            raise ValueError("Unexpected port")
        hostname = parsed.hostname
        if hostname.endswith(".onion"):
            return
        for record in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM):
            if not ipaddress.ip_address(record[4][0]).is_global:
                raise ValueError("Private or loopback target prohibited")

    def study(self, url, skill):
        self.academy.check_url(url, skill)
        route = SecurityPolicy.research_route(url, tor_enabled=self.tor_enabled)
        self.validate_public_url(url)
        if route == "tor" and self.transport is None:
            raise RuntimeError("Tor transport must be explicitly configured")
        # Academy applies a second allowlist check to final redirect URL.
        # Its fetcher also limits response size and requires HTML.
        if self.transport is None:
            result = self.academy.ingest(url, skill)
        else:
            result = self.academy.ingest(url, skill, opener=self.transport)
        return ResearchResult(result["url"], route, "pending_review", result["characters"])

    def study_batch(self, entries, *, max_pages=5):
        if not 1 <= max_pages <= 20:
            raise ValueError("Invalid research budget")
        outcomes = []
        for url, skill in list(entries)[:max_pages]:
            try:
                outcomes.append(self.study(url, skill))
            except (ValueError, RuntimeError, OSError, HTTPError) as exc:
                outcomes.append({"url": url, "skill": skill, "error": type(exc).__name__})
        return outcomes
