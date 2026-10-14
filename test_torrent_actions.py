import unittest
from unittest.mock import Mock
from jarvis.torrent_actions import ApprovedTorrentActions
from jarvis.torrent_client import TorrentClient


class TorrentPermissionTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock(spec=TorrentClient)
        self.client._hash.side_effect = TorrentClient._hash
        self.actions = ApprovedTorrentActions(self.client, "SID=local")
        self.hash = "a" * 40

    def test_requires_explicit_approval(self):
        with self.assertRaises(PermissionError):
            self.actions.execute_pause("missing", self.hash, True)
        self.client.set_paused.assert_not_called()

    def test_approval_is_single_use(self):
        request = self.actions.propose_pause(self.hash, True)
        self.assertTrue(self.actions.gate.approve(request.token))
        self.actions.execute_pause(request.token, self.hash, True)
        self.client.set_paused.assert_called_once_with("SID=local", self.hash, True)
        with self.assertRaises(PermissionError):
            self.actions.execute_pause(request.token, self.hash, True)

    def test_pause_approval_cannot_resume(self):
        request = self.actions.propose_pause(self.hash, True)
        self.actions.gate.approve(request.token)
        with self.assertRaises(PermissionError):
            self.actions.execute_pause(request.token, self.hash, False)
        self.client.set_paused.assert_not_called()

    def test_close_revokes_pending_approval(self):
        request = self.actions.propose_pause(self.hash, True)
        self.actions.gate.approve(request.token)
        self.actions.close()
        with self.assertRaises(PermissionError):
            self.actions.execute_pause(request.token, self.hash, True)


if __name__ == "__main__":
    unittest.main()
