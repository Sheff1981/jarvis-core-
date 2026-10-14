import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from jarvis.local_llm import LocalLLM


class FakeResponse:
    def __init__(self, content="  Привет!  "):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, *args):
        return json.dumps({"message": {"content": self.content}}).encode()


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
        with patch("jarvis.local_llm.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "недоступна"):
                LocalLLM().ask("Привет")

    def test_second_request_includes_first_exchange(self):
        requests = []
        def fake_open(request, timeout):
            requests.append(json.loads(request.data)["messages"])
            return FakeResponse("Ответ")
        with patch("jarvis.local_llm.urlopen", side_effect=fake_open):
            llm = LocalLLM()
            llm.ask("Первый вопрос")
            llm.ask("А что дальше?")
        self.assertEqual([item["role"] for item in requests[1]],
                         ["system", "user", "assistant", "user"])
        self.assertEqual(requests[1][1]["content"], "Первый вопрос")

    def test_history_is_bounded(self):
        with patch("jarvis.local_llm.urlopen", return_value=FakeResponse()):
            llm = LocalLLM(max_turns=2)
            for number in range(5):
                llm.ask(str(number))
            self.assertEqual(len(llm.history), 4)
            self.assertEqual(llm.history[0]["content"], "3")
            llm.clear_history()
            self.assertEqual(llm.history, [])

    def test_failed_request_not_recorded(self):
        with patch("jarvis.local_llm.urlopen", side_effect=URLError("offline")):
            llm = LocalLLM()
            with self.assertRaises(RuntimeError):
                llm.ask("Неудачный запрос")
            self.assertEqual(llm.history, [])


if __name__ == "__main__":
    unittest.main()
