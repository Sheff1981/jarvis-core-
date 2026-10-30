"""Permission-controlled torrent mutations, independent of dialogue or LLM."""
import hashlib
import json
from jarvis.permissions import PermissionGate


class ApprovedTorrentActions:
    def __init__(self, client, cookie, gate=None):
        self.client = client
        self.cookie = cookie
        self.gate = gate if gate is not None else PermissionGate()

    def propose_pause(self, infohash, paused):
        normalized = self.client._hash(infohash)
        if type(paused) is not bool:
            raise ValueError("Paused must be boolean")
        operation = "torrent_pause" if paused else "torrent_resume"
        return self.gate.propose(operation, normalized, operation + ": " + normalized)

    def execute_pause(self, token, infohash, paused):
        normalized = self.client._hash(infohash)
        if type(paused) is not bool:
            raise ValueError("Paused must be boolean")
        operation = "torrent_pause" if paused else "torrent_resume"
        if not self.gate.consume(token, operation, normalized):
            raise PermissionError("Explicit one-time approval required")
        return self.client.set_paused(self.cookie, normalized, paused)

    @staticmethod
    def _fingerprint(operation, parameters):
        encoded = json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(operation.encode("utf-8") + b":" + encoded).hexdigest()

    def propose_magnet(self, magnet, save_path=None):
        self.client.validate_magnet(magnet)
        target = self._fingerprint("torrent_add", [magnet, save_path])
        return self.gate.propose("torrent_add", target, "Add paused torrent to: " + str(save_path))

    def execute_magnet(self, token, magnet, save_path=None):
        target = self._fingerprint("torrent_add", [magnet, save_path])
        if not self.gate.consume(token, "torrent_add", target):
            raise PermissionError("Explicit one-time approval required")
        return self.client.add_magnet(self.cookie, magnet, save_path)

    def propose_file_priority(self, infohash, indices, priority):
        normalized = self.client._hash(infohash)
        if not isinstance(indices, (list, tuple)) or not indices or any(
            type(index) is not int or index < 0 for index in indices
        ) or priority not in (0, 1, 6, 7):
            raise ValueError("Invalid file selection")
        target = self._fingerprint("torrent_files", [normalized, list(indices), priority])
        return self.gate.propose("torrent_files", target, "Change selected torrent files: " + normalized)

    def execute_file_priority(self, token, infohash, indices, priority):
        normalized = self.client._hash(infohash)
        target = self._fingerprint("torrent_files", [normalized, list(indices), priority])
        if not self.gate.consume(token, "torrent_files", target):
            raise PermissionError("Explicit one-time approval required")
        return self.client.set_file_priority(self.cookie, normalized, indices, priority)

    def close(self):
        self.gate.revoke_all()
