"""Offline tests for Ollama project dialogue integration."""
import io
import json
import os
import tempfile
import unittest

from jarvis.dialogue_memory import DialogueMemory
from jarvis.ollama_dialogue import OllamaError, ask_project
from jarvis.projects import Projects


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class OllamaDialogueTests(unittest.TestCase):
    def test_request_context_and_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "test.db")
            projects = Projects(path)
            project_id = projects.add("JARVIS", "Test Ollama")
            projects.close()
            captured = {}

            def fake_transport(req, timeout):
                captured.update(json.loads(req.data.decode("utf-8")))
                self.assertEqual(timeout, 120)
                return Response(json.dumps({"message": {"content": "Готово"}}).encode())

            answer = ask_project(project_id, "Что дальше?", db_path=path,
                                 transport=fake_transport)
            self.assertEqual(answer, "Готово")
            self.assertEqual(captured["messages"][-1]["content"], "Что дальше?")
            self.assertIn("Test Ollama", captured["messages"][0]["content"])
            memory = DialogueMemory(path)
            try:
                self.assertEqual([x["role"] for x in memory.recent(project_id)],
                                 ["user", "assistant"])
            finally:
                memory.close()

    def test_failure_does_not_save_turns(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "test.db")
            projects = Projects(path)
            project_id = projects.add("JARVIS")
            projects.close()

            def failed(*_args, **_kwargs):
                raise OSError("offline")

            with self.assertRaises(OllamaError):
                ask_project(project_id, "Hi", db_path=path, transport=failed)
            memory = DialogueMemory(path)
            try:
                self.assertEqual(memory.recent(project_id), [])
            finally:
                memory.close()

    def test_reject_nonlocal_endpoint(self):
        with self.assertRaises(ValueError):
            ask_project("x", "Hi", endpoint="https://example.com/api/chat")


if __name__ == "__main__":
    unittest.main()
