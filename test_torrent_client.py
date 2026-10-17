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
        with patch.object(client, "api_version", return_value=(2, 10)), patch.object(client, "_request", return_value=(b"", "")) as request:
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

    def test_progress_reports_unknown_eta_as_none(self):
        client = TorrentClient()
        sample = [{"hash": "a" * 40, "name": "Course", "progress": 0.375,
                   "dlspeed": 2048, "state": "downloading", "eta": 8640000}]
        with patch.object(client, "list_torrents", return_value=sample):
            result = client.progress("SID=local")
        self.assertEqual(result[0]["progress_percent"], 37.5)
        self.assertEqual(result[0]["download_speed_bps"], 2048)
        self.assertIsNone(result[0]["eta_seconds"])

    def test_progress_rejects_invalid_fraction(self):
        client = TorrentClient()
        with patch.object(client, "list_torrents", return_value=[
            {"hash": "a" * 40, "progress": 1.5}
        ]):
            with self.assertRaises(ValueError):
                client.progress("SID=local")

    def test_magnet_rejects_missing_or_duplicate_hash(self):
        for uri in ("magnet:?xt=urn:btih:short",
                    "magnet:?dn=example",
                    "magnet:?xt=urn:btih:" + "a" * 40 + "&xt=urn:btih:" + "b" * 40):
            with self.subTest(uri=uri):
                with self.assertRaises(ValueError):
                    TorrentClient.validate_magnet(uri)

    def test_magnet_accepts_base32_infohash(self):
        uri = "magnet:?xt=urn:btih:" + "A" * 32
        self.assertEqual(TorrentClient.validate_magnet(uri), uri)

    def test_modern_qbittorrent_uses_stop_and_start(self):
        client = TorrentClient()
        with patch.object(client, "api_version", return_value=(2, 11)), patch.object(
            client, "_request", return_value=(b"", "")
        ) as request:
            client.set_paused("SID=local", "a" * 40, True)
            self.assertEqual(request.call_args.args[0], "/api/v2/torrents/stop")
            client.set_paused("SID=local", "a" * 40, False)
            self.assertEqual(request.call_args.args[0], "/api/v2/torrents/start")

    def test_api_version_parsing(self):
        client = TorrentClient()
        with patch.object(client, "_request", return_value=(b"2.11.4", "")):
            self.assertEqual(client.api_version("SID=local"), (2, 11, 4))

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
