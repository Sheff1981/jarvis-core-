import unittest
from unittest.mock import patch
from jarvis.torrent_client import TorrentClient


class TorrentClientTests(unittest.TestCase):
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
