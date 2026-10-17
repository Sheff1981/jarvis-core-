"""CPU-only fallback regression tests for unsupported NVIDIA CUDA toolchains."""
import json
import sys
import unittest
from unittest.mock import patch, MagicMock

import chat
from jarvis.local_model import Ollama
from jarvis.local_llm import LocalLLM


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return json.dumps({"message": {"content": "Здравствуйте!"}}).encode("utf-8")


class CpuOnlyProfileTests(unittest.TestCase):
    def _check_payload(self, payload):
        self.assertEqual(payload["options"]["num_gpu"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 1024)
        self.assertEqual(payload["options"]["num_thread"], 4)
        self.assertLessEqual(payload["options"]["num_predict"], 128)
        self.assertEqual(payload["keep_alive"], 0)
        self.assertFalse(payload["stream"])

    def test_dialogue_adapter_uses_cpu_profile(self):
        model = Ollama(model="qwen2.5:3b-instruct-q6_K", timeout=120, cpu_only=True)
        with patch("jarvis.local_model.open_local", return_value=FakeResponse()) as request:
            self.assertEqual(model.reply([{"role": "user", "content": "Привет"}]), "Здравствуйте!")
        payload = json.loads(request.call_args.args[0].data)
        self._check_payload(payload)
        self.assertEqual(request.call_args.kwargs["timeout"], 120)

    def test_unified_adapter_uses_cpu_profile(self):
        model = LocalLLM(model="qwen2.5:3b-instruct-q6_K", timeout=120, cpu_only=True)
        with patch("jarvis.local_llm.open_local", return_value=FakeResponse()) as request:
            self.assertEqual(model.ask("Привет"), "Здравствуйте!")
        self._check_payload(json.loads(request.call_args.args[0].data))
        self.assertEqual(request.call_args.kwargs["timeout"], 120)

    def test_default_does_not_change_gpu_options(self):
        with patch("jarvis.local_model.open_local", return_value=FakeResponse()) as request:
            Ollama().reply([{"role": "user", "content": "Привет"}])
        payload = json.loads(request.call_args.args[0].data)
        self.assertNotIn("num_gpu", payload["options"])
        self.assertNotIn("keep_alive", payload)

    def test_cli_dialogue_cpu_option(self):
        with patch.object(sys, "argv", ["chat.py", "--model", "qwen2.5:3b-instruct-q6_K", "--cpu-only"]), \
             patch("chat.Dialogue") as dialogue, \
             patch("builtins.input", side_effect=EOFError):
            chat.main()
            model = dialogue.call_args.kwargs["model"]
            self.assertTrue(model.cpu_only)
            self.assertEqual(model.timeout, 120)

    def test_cli_assistant_cpu_option(self):
        with patch.object(sys, "argv", ["chat.py", "--assistant", "--model", "qwen2.5:3b-instruct-q6_K", "--cpu-only"]), \
             patch("chat.Assistant") as assistant, \
             patch("builtins.input", side_effect=EOFError):
            assistant.return_value = MagicMock()
            chat.main()
            model = assistant.call_args.kwargs["llm"]
            self.assertTrue(model.cpu_only)
            self.assertEqual(model.timeout, 120)


if __name__ == "__main__":
    unittest.main()
