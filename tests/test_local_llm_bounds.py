import unittest
from unittest.mock import patch

from jarvis.local_llm import LocalLLM


class LocalLLMBoundsTests(unittest.TestCase):
    def test_invalid_timeout_rejected(self):
        for timeout in (0, -1, 121):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                LocalLLM(timeout=timeout)

    def test_missing_model_rejected(self):
        with self.assertRaises(ValueError):
            LocalLLM(model=" ")

    def test_non_text_prompt_rejected(self):
        with self.assertRaises(TypeError):
            LocalLLM().ask(None)

    def test_large_response_rejected_without_history_mutation(self):
        class LargeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return b"x" * (1024 * 1024 + 1)

        llm = LocalLLM()
        with patch("jarvis.local_llm.urlopen", return_value=LargeResponse()):
            with self.assertRaisesRegex(RuntimeError, "слишком большой"):
                llm.ask("Привет")
        self.assertEqual(llm.history, [])
