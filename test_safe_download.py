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
