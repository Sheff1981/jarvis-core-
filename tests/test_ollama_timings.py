"""Ollama timing metrics regression tests."""
import json
import unittest
from unittest.mock import patch

from jarvis.local_llm import LocalLLM


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return json.dumps({
            "message": {"content": "Готово."},
            "total_duration": 1500000000,
            "load_duration": 800000000,
            "prompt_eval_duration": 100000000,
            "eval_duration": 500000000,
            "eval_count": 20,
            "prompt_eval_count": 40,
        }).encode("utf-8")


class OllamaTimingTests(unittest.TestCase):
    def test_timings_are_reported_in_milliseconds(self):
        model = LocalLLM(cpu_only=True)
        with patch("jarvis.local_llm.open_local", return_value=FakeResponse()):
            self.assertEqual(model.ask("Привет"), "Готово.")
        self.assertEqual(model.last_metrics["load_ms"], 800.0)
        self.assertEqual(model.last_metrics["eval_ms"], 500.0)
        self.assertEqual(model.last_metrics["total_ms"], 1500.0)
        self.assertEqual(model.last_metrics["eval_count"], 20)
        self.assertGreaterEqual(model.last_metrics["wall_ms"], 0)

    def test_no_metrics_before_first_request(self):
        self.assertIsNone(LocalLLM().last_metrics)


if __name__ == "__main__":
    unittest.main()
