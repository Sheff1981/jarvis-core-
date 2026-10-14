import unittest
from unittest.mock import patch
from jarvis.torrent_client import TorrentClient


class TorrentClientTests(unittest.TestCase):
    def test_login_returns_session_cookie(self):
        client = TorrentClient()
        with patch.object(client, "_request", return_value=(b"Ok.", "SID=secret; HttpOnly")) as request:
            self.assertEqual(client.login("localuser", "private-password"), "SID=secret")
            self.assertEqual(request.call_args.args[0], "/api/v2/auth/login")

    def test_login_rejects_bad_credentials(self):
        client = TorrentClient()
        with patch.object(client, "_request", return_value=(b"Fails.", "")):
            with self.assertRaises(PermissionError):
                client.login("localuser", "incorrect")

    def test_pause_and_resume_target_exact_hash(self):
        client = TorrentClient()
        infohash = "a" * 40
        with patch.object(client, "_request", return_value=(b"", "")) as request:
            client.set_paused("SID=local", infohash, True)
            self.assertEqual(request.call_args.args[0], "/api/v2/torrents/pause")
            self.assertEqual(request.call_args.args[1], {"hashes": infohash})
            client.set_paused("SID=local", infohash, False)
            self.assertEqual(request.call_args.args[0], "/api/v2/torrents/resume")

    def test_file_selection_validates_indices(self):
        client = TorrentClient()
        with self.assertRaises(ValueError):
            client.set_file_priority("SID=local", "a" * 40, [-1], 0)
        with patch.object(client, "_request", return_value=(b"", "")) as request:
            client.set_file_priority("SID=local", "a" * 40, [0, 2], 0)
            self.assertEqual(request.call_args.args[1]["id"], "0|2")

    def test_rejects_ambiguous_torrent_identifier(self):
        client = TorrentClient()
        with self.assertRaises(ValueError):
            client.set_paused("SID=local", "course-name", True)

    def test_only_loopback_endpoint(self):
        with self.assertRaises(ValueError):
            TorrentClient("http://192.168.1.10:8080")

    def test_rejects_non_magnet(self):
        with self.assertRaises(ValueError):
            TorrentClient().add_magnet("SID=example", "https://example.com/file")

    def test_new_torrent_is_paused(self):
        client = TorrentClient()
        with patch.object(client, "_request", return_value=(b"Ok.", "")) as request:
            self.assertTrue(client.add_magnet("SID=example", "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"))
            args = request.call_args.args
            self.assertEqual(args[0], "/api/v2/torrents/add")
            self.assertEqual(args[1]["paused"], "true")

    def test_invalid_response_is_rejected(self):
        client = TorrentClient()
        with patch.object(client, "_request", return_value=(b"Fails.", "")):
            with self.assertRaises(RuntimeError):
                client.add_magnet("SID=example", "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567")


if __name__ == "__main__":
    unittest.main()
