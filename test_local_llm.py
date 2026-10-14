import json
import unittest
from unittest.mock import patch
from jarvis.local_llm import LocalLLM


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, *args):
        return json.dumps({"message": {"content": "  Привет!  "}}).encode()


class LocalLLMTests(unittest.TestCase):
    def test_rejects_remote_endpoint(self):
        with self.assertRaises(ValueError):
            LocalLLM(endpoint="https://remote.example")

    def test_uses_local_api_and_returns_answer(self):
        with patch("jarvis.local_llm.urlopen", return_value=FakeResponse()) as mocked:
            self.assertEqual(LocalLLM().ask("Привет"), "Привет!")
            request = mocked.call_args.args[0]
            self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
            self.assertEqual(json.loads(request.data)["messages"][-1]["content"], "Привет")

    def test_connection_error_is_readable(self):
        from urllib.error import URLError
        with patch("jarvis.local_llm.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "недоступна"):
                LocalLLM().ask("Привет")


if __name__ == "__main__":
    unittest.main()
