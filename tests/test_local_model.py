import json
import unittest
from unittest.mock import patch
from jarvis.local_model import Ollama, LocalModelError


class ModelTests(unittest.TestCase):
    def test_rejects_remote_endpoint(self):
        for url in ("https://example.com", "http://192.168.1.2:11434", "http://localhost.evil.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                Ollama(endpoint=url)

    def test_rejects_invalid_messages(self):
        with self.assertRaises(ValueError):
            Ollama().reply([{"role": "tool", "content": "run"}])

    def test_local_response(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return json.dumps({"message": {"content": "Привет!"}}).encode()
        with patch("jarvis.local_model.open_local", return_value=Response()) as call:
            self.assertEqual(Ollama().reply([{"role": "user", "content": "Привет"}]), "Привет!")
            self.assertEqual(call.call_args.kwargs["timeout"], 15)

    def test_unavailable_is_safe_error(self):
        with patch("jarvis.local_model.open_local", side_effect=OSError("offline")):
            with self.assertRaises(LocalModelError):
                Ollama().reply([{"role": "user", "content": "Привет"}])
