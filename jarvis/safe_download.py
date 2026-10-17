"""Conservative HTTPS downloader: approval per URL, bounded size, no execution."""
import hashlib
import http.client
import ssl
import ipaddress
import os
from pathlib import Path
import socket
import tempfile
from urllib.parse import urlsplit

from jarvis.permissions import PermissionGate


MAX_BYTES = 100 * 1024 * 1024


def validate_url(url):
    if not isinstance(url, str) or any(ord(ch) < 33 or ord(ch) == 127 for ch in url):
        raise ValueError("Invalid URL characters")
    parsed = urlsplit(url)
    if parsed.fragment or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only public HTTPS URLs on port 443 are permitted")
    host = parsed.hostname
    if host.lower() == "localhost" or host.lower().endswith(".localhost"):
        raise ValueError("Local hosts are prohibited")
    records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not records:
        raise ValueError("Host has no addresses")
    for record in records:
        address = ipaddress.ip_address(record[4][0])
        if not address.is_global:
            raise ValueError("Nonpublic network addresses are prohibited")
    return url


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """TLS checks the hostname while TCP uses a vetted public IP."""

    def __init__(self, hostname, address):
        super().__init__(hostname, port=443, timeout=20, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        self.sock = socket.create_connection((self.address, 443), self.timeout)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


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
                parsed = urlsplit(url)
                records = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
                if not records or any(
                    not ipaddress.ip_address(record[4][0]).is_global for record in records
                ):
                    raise ValueError("Nonpublic network addresses are prohibited")
                connection = PinnedHTTPSConnection(parsed.hostname, records[0][4][0])
                try:
                    path = parsed.path or "/"
                    if parsed.query:
                        path += "?" + parsed.query
                    connection.request("GET", path, headers={"User-Agent": "JARVIS/0.1"})
                    response = connection.getresponse()
                    if response.status != 200:
                        raise ValueError("Unexpected HTTP status or redirect")
                    length = response.getheader("Content-Length")
                    if length is not None:
                        if not length.isdecimal() or int(length) > MAX_BYTES:
                            raise ValueError("Invalid or excessive Content-Length")
                    while True:
                        chunk = response.read(min(65536, MAX_BYTES + 1 - count))
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > MAX_BYTES:
                            raise ValueError("Download exceeds 100 MiB")
                        digest.update(chunk)
                        output.write(chunk)
                    if length is not None and count != int(length):
                        raise ValueError("Incomplete download")
                finally:
                    connection.close()
            # Atomic no-overwrite publication; destination must not already exist.
            os.link(temporary, target)
            return {"path": str(target), "bytes": count, "sha256": digest.hexdigest()}
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
