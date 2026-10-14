import tempfile
import unittest
from unittest.mock import patch
from jarvis.safe_download import DownloadManager, validate_url


class DownloadSafetyTests(unittest.TestCase):
    def test_pinned_connection_uses_approved_address(self):
        from jarvis.safe_download import PinnedHTTPSConnection
        with patch("jarvis.safe_download.socket.create_connection") as connect:
            with patch("jarvis.safe_download.ssl.create_default_context") as context:
                connection = PinnedHTTPSConnection("example.com", "93.184.215.14")
                connection.connect()
                connect.assert_called_once_with(("93.184.215.14", 443), 20)
                context.return_value.wrap_socket.assert_called_once_with(
                    connect.return_value, server_hostname="example.com"
                )

    def test_rejects_fragment_and_control_characters(self):
        for url in ("https://example.com/a#fragment", "https://example.com/\nheader"):
            with self.assertRaises(ValueError):
                validate_url(url)

    def test_rejects_empty_dns_response(self):
        with patch("jarvis.safe_download.socket.getaddrinfo", return_value=[]):
            with self.assertRaisesRegex(ValueError, "no addresses"):
                validate_url("https://example.com/file")

    def test_existing_file_is_not_overwritten(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "archive.zip"
            target.write_bytes(b"original")
            manager = DownloadManager(directory)
            url = "https://example.com/archive.zip"
            with patch("jarvis.safe_download.validate_url", return_value=url):
                approval = manager.propose(url)
                manager.gate.approve(approval.token)
                with self.assertRaises(FileExistsError):
                    manager.download(approval.token, url, "archive.zip")
            self.assertEqual(b"original", target.read_bytes())

    def test_partial_transfer_leaves_no_file(self):
        from pathlib import Path
        from unittest.mock import MagicMock
        url = "https://example.com/archive.zip"
        with tempfile.TemporaryDirectory() as folder:
            manager = DownloadManager(folder)
            response = MagicMock()
            response.status = 200
            response.getheader.return_value = "12"
            response.read.side_effect = [b"short", b""]
            connection = MagicMock()
            connection.getresponse.return_value = response
            with patch("jarvis.safe_download.validate_url", return_value=url):
                with patch("jarvis.safe_download.socket.getaddrinfo", return_value=[
                    (2, 1, 6, "", ("93.184.215.14", 443))
                ]):
                    with patch("jarvis.safe_download.PinnedHTTPSConnection", return_value=connection):
                        request = manager.propose(url)
                        manager.gate.approve(request.token)
                        with self.assertRaisesRegex(ValueError, "Incomplete download"):
                            manager.download(request.token, url, "archive.zip")
            self.assertEqual([], list(Path(folder).iterdir()))

    def test_requires_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(directory)
            with self.assertRaises(PermissionError):
                manager.download("not-approved", "https://example.com/a", "a.bin")

    def test_rejects_insecure_and_local_hosts(self):
        for url in ("http://example.com/a", "https://localhost/a",
                    "https://127.0.0.1/a", "https://user:pass@example.com/a"):
            with self.assertRaises(ValueError):
                validate_url(url)

    def test_rejects_path_traversal_after_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(directory)
            with patch("jarvis.safe_download.validate_url", return_value="https://example.com/a"):
                request = manager.propose("https://example.com/a")
                self.assertTrue(manager.gate.approve(request.token))
                with self.assertRaises(ValueError):
                    manager.download(request.token, "https://example.com/a", "../outside.exe")


if __name__ == "__main__":
    unittest.main()
