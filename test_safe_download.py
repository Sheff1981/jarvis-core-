import tempfile
import unittest
from unittest.mock import patch
from jarvis.safe_download import DownloadManager, validate_url


class DownloadSafetyTests(unittest.TestCase):
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
