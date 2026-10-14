"""Permission-controlled torrent mutations, independent of dialogue or LLM."""
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

    def close(self):
        self.gate.revoke_all()
