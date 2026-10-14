"""Local-only qBittorrent Web API adapter. No automatic downloads or execution."""
import json
import re
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, build_opener, ProxyHandler


class TorrentClient:
    def __init__(self, endpoint="http://127.0.0.1:8080", timeout=8):
        if endpoint != "http://127.0.0.1:8080":
            raise ValueError("Only local qBittorrent endpoint is allowed")
        self.endpoint = endpoint
        self.timeout = timeout

    def _request(self, path, payload=None, cookie=None):
        headers = {"User-Agent": "JARVIS-local/0.1"}
        if cookie:
            headers["Cookie"] = cookie
        data = urlencode(payload).encode("utf-8") if payload is not None else None
        request = Request(self.endpoint + path, data=data, headers=headers)
        opener = build_opener(ProxyHandler({}))
        with opener.open(request, timeout=self.timeout) as response:
            return response.read(), response.headers.get("Set-Cookie", "")

    def login(self, username, password):
        if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
            raise ValueError("Credentials are required")
        body, cookie = self._request(
            "/api/v2/auth/login", {"username": username, "password": password}
        )
        if body.strip() != b"Ok." or not cookie.startswith("SID="):
            raise PermissionError("qBittorrent authentication failed")
        return cookie.split(";", 1)[0]

    def list_torrents(self, cookie):
        body, _ = self._request("/api/v2/torrents/info", cookie=cookie)
        result = json.loads(body.decode("utf-8"))
        if not isinstance(result, list):
            raise ValueError("Unexpected torrent response")
        return result

    def progress(self, cookie):
        """Return bounded status records without guessing missing ETA values."""
        entries = self.list_torrents(cookie)
        statuses = []
        for entry in entries[:200]:
            if not isinstance(entry, dict):
                raise ValueError("Invalid torrent status")
            fraction = entry.get("progress")
            if not isinstance(fraction, (float, int)) or isinstance(fraction, bool) or not 0 <= fraction <= 1:
                raise ValueError("Invalid progress fraction")
            statuses.append({
                "hash": self._hash(entry.get("hash")),
                "name": str(entry.get("name", ""))[:300],
                "progress_percent": round(fraction * 100, 1),
                "download_speed_bps": max(0, int(entry.get("dlspeed", 0))),
                "state": str(entry.get("state", "unknown"))[:80],
                "eta_seconds": entry.get("eta") if isinstance(entry.get("eta"), int)
                    and not isinstance(entry.get("eta"), bool) and 0 <= entry["eta"] < 8640000 else None,
            })
        return statuses

    @staticmethod
    def _hash(value):
        if not isinstance(value, str) or len(value) not in (40, 64):
            raise ValueError("A full torrent infohash is required")
        if any(ch not in "0123456789abcdefABCDEF" for ch in value):
            raise ValueError("Invalid torrent infohash")
        return value.lower()

    def files(self, cookie, infohash):
        from urllib.parse import quote
        infohash = self._hash(infohash)
        body, _ = self._request("/api/v2/torrents/files?hash=" + quote(infohash), cookie=cookie)
        files = json.loads(body.decode("utf-8"))
        if not isinstance(files, list):
            raise ValueError("Invalid torrent file list")
        return files

    def set_file_priority(self, cookie, infohash, indices, priority):
        infohash = self._hash(infohash)
        if not isinstance(indices, (list, tuple)) or not indices or any(
            type(index) is not int or index < 0 for index in indices
        ):
            raise ValueError("File indices must be nonnegative integers")
        if priority not in (0, 1, 6, 7):
            raise ValueError("Unsupported file priority")
        payload = {"hash": infohash, "id": "|".join(map(str, indices)), "priority": str(priority)}
        body, _ = self._request("/api/v2/torrents/filePrio", payload, cookie)
        if body.strip():
            raise RuntimeError("Torrent client rejected file priority")
        return True

    def set_paused(self, cookie, infohash, paused):
        infohash = self._hash(infohash)
        if type(paused) is not bool:
            raise ValueError("Paused must be a boolean")
        endpoint = "/api/v2/torrents/pause" if paused else "/api/v2/torrents/resume"
        body, _ = self._request(endpoint, {"hashes": infohash}, cookie)
        if body.strip():
            raise RuntimeError("Torrent client rejected state change")
        return True

    @staticmethod
    def validate_magnet(magnet):
        if not isinstance(magnet, str) or len(magnet) > 4096 or any(ord(ch) < 32 for ch in magnet):
            raise ValueError("Invalid magnet link")
        parsed = urlsplit(magnet)
        if parsed.scheme != "magnet" or parsed.netloc or parsed.fragment:
            raise ValueError("Invalid magnet URI")
        identifiers = parse_qs(parsed.query, keep_blank_values=True).get("xt", [])
        if len(identifiers) != 1:
            raise ValueError("Exactly one BitTorrent identifier required")
        identifier = identifiers[0]
        if not re.fullmatch(r"urn:btih:(?:[a-fA-F0-9]{40}|[a-zA-Z2-7]{32})", identifier):
            raise ValueError("Invalid BitTorrent infohash")
        return magnet

    def add_magnet(self, cookie, magnet, save_path=None):
        self.validate_magnet(magnet)
        payload = {"urls": magnet, "paused": "true"}
        if save_path is not None:
            payload["savepath"] = str(save_path)
        body, _ = self._request("/api/v2/torrents/add", payload, cookie)
        if body.strip() != b"Ok.":
            raise RuntimeError("Torrent client rejected the magnet")
        return True
