"""Local-only qBittorrent Web API adapter. No automatic downloads or execution."""
import json
from urllib.parse import urlencode
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import URLError


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

    def list_torrents(self, cookie):
        body, _ = self._request("/api/v2/torrents/info", cookie=cookie)
        result = json.loads(body.decode("utf-8"))
        if not isinstance(result, list):
            raise ValueError("Unexpected torrent response")
        return result

    def add_magnet(self, cookie, magnet, save_path=None):
        if not isinstance(magnet, str) or not magnet.startswith("magnet:?xt=urn:btih:"):
            raise ValueError("Only BitTorrent infohash magnet links are accepted")
        if len(magnet) > 4096 or any(ord(ch) < 32 for ch in magnet):
            raise ValueError("Invalid magnet link")
        payload = {"urls": magnet, "paused": "true"}
        if save_path is not None:
            payload["savepath"] = str(save_path)
        body, _ = self._request("/api/v2/torrents/add", payload, cookie)
        if body.strip() != b"Ok.":
            raise RuntimeError("Torrent client rejected the magnet")
        return True
