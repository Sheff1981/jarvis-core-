"""Conservative HTTPS downloader: approval per URL, bounded size, no execution."""
import hashlib
import ipaddress
import os
from pathlib import Path
import socket
import tempfile
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

from jarvis.permissions import PermissionGate


MAX_BYTES = 100 * 1024 * 1024


def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only public HTTPS URLs on port 443 are permitted")
    host = parsed.hostname
    if host.lower() == "localhost" or host.lower().endswith(".localhost"):
        raise ValueError("Local hosts are prohibited")
    for record in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        address = ipaddress.ip_address(record[4][0])
        if not address.is_global:
            raise ValueError("Nonpublic network addresses are prohibited")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("Redirects require a separate approval")


class DownloadManager:
    def __init__(self, destination, gate=None):
        self.destination = Path(destination).expanduser().resolve()
        self.gate = gate if gate is not None else PermissionGate()

    def propose(self, url):
        validate_url(url)
        return self.gate.propose("download_https", url, "Download from " + url)

    def download(self, token, url, filename):
        if not self.gate.consume(token, "download_https", url):
            raise PermissionError("Separate download approval required")
        validate_url(url)
        if not filename or Path(filename).name != filename or filename in (".", ".."):
            raise ValueError("Filename must be a simple basename")
        if not self.destination.is_dir():
            raise NotADirectoryError(str(self.destination))
        target = self.destination / filename
        if target.exists():
            raise FileExistsError(str(target))
        fd, temporary = tempfile.mkstemp(prefix=".jarvis-", suffix=".part", dir=self.destination)
        digest = hashlib.sha256()
        count = 0
        try:
            with os.fdopen(fd, "wb") as output:
                opener = build_opener(NoRedirect)
                with opener.open(Request(url, headers={"User-Agent": "JARVIS/0.1"}), timeout=20) as response:
                    if response.geturl() != url:
                        raise ValueError("Unexpected redirect")
                    while True:
                        chunk = response.read(min(65536, MAX_BYTES + 1 - count))
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > MAX_BYTES:
                            raise ValueError("Download exceeds 100 MiB")
                        digest.update(chunk)
                        output.write(chunk)
            # Atomic no-overwrite publication; destination must not already exist.
            os.link(temporary, target)
            return {"path": str(target), "bytes": count, "sha256": digest.hexdigest()}
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
