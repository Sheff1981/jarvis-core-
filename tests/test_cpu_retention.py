"""CPU model retention remains opt-in and bounded."""
import json
import unittest
from unittest.mock import patch

from jarvis.local_llm import LocalLLM


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return json.dumps({"message": {"content": "Да."}}).encode()


class CpuRetentionTests(unittest.TestCase):
    def test_default_remains_zero(self):
        self.assertEqual(LocalLLM(cpu_only=True).keep_alive_seconds, 0)

    def test_invalid_retention_is_rejected(self):
        for value in (-1, 301, 1.5, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    LocalLLM(cpu_only=True, keep_alive_seconds=value)

    def test_opt_in_retention_is_forwarded(self):
        for seconds in (0, 30, 120, 300):
            with self.subTest(seconds=seconds):
                llm = LocalLLM(cpu_only=True, keep_alive_seconds=seconds)
                captured = []

                def fake_open(request, timeout):
                    captured.append(json.loads(request.data))
                    return Response()

                with patch("jarvis.local_llm.open_local", side_effect=fake_open):
                    self.assertEqual(llm.ask("Привет"), "Да.")
                self.assertEqual(captured[0]["keep_alive"], seconds)
                self.assertEqual(captured[0]["options"]["num_gpu"], 0)


if __name__ == "__main__":
    unittest.main()
