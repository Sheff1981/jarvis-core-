"""Integration checks for optional Neural Core backends and shadow mode."""
import io
import json
import unittest

from jarvis.neural_backends import CallableAdapter, OllamaAdapter
from jarvis.neural_shadow import evaluate_shadow
from jarvis.neural_telemetry import measured_inference
from jarvis.process_memory import ProcessMemory


class FakeResponse:
    def __init__(self, value):
        self.buffer = io.BytesIO(json.dumps(value).encode("utf-8"))
    def __enter__(self):
        return self.buffer
    def __exit__(self, *args):
        self.buffer.close()


class NeuralFreezeTests(unittest.TestCase):
    def test_local_ollama_protocol(self):
        seen = []
        def transport(req, timeout):
            seen.append(json.loads(req.data))
            return FakeResponse({"response": "готово"})
        result = OllamaAdapter("qwen3:1.7b", transport=transport).infer("привет")
        self.assertEqual(result.text, "готово")
        self.assertFalse(seen[0]["stream"])
        self.assertEqual(seen[0]["model"], "qwen3:1.7b")

    def test_invalid_ollama_response(self):
        adapter = OllamaAdapter("model", transport=lambda req, timeout: FakeResponse({}))
        with self.assertRaises(ValueError):
            adapter.infer("test")

    def test_shadow_never_routes_live(self):
        adapter = CallableAdapter(lambda prompt: prompt)
        report = evaluate_shadow(adapter, [(str(i), str(i)) for i in range(12)])
        self.assertTrue(report.eligible)
        self.assertEqual(report.total, 12)

    def test_shadow_rejects_failures(self):
        def fail(_):
            raise RuntimeError("failure")
        report = evaluate_shadow(CallableAdapter(fail), [(str(i), str(i)) for i in range(12)])
        self.assertFalse(report.eligible)
        self.assertEqual(report.errors, 12)

    def test_telemetry(self):
        ticks = iter((1.0, 1.125))
        adapter = CallableAdapter(lambda text: text.upper(), backend="test")
        result, telemetry = measured_inference(
            adapter, "ok", clock=lambda: next(ticks),
            memory_probe=lambda: ProcessMemory(1024, "test"))
        self.assertEqual(result.text, "OK")
        self.assertEqual(telemetry.duration_ms, 125.0)
        self.assertEqual(telemetry.rss_after_bytes, 1024)


if __name__ == "__main__":
    unittest.main()
