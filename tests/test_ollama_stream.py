"""Streaming integration tests without a running model."""
import io
import json
import os
import tempfile
import unittest

from jarvis.dialogue_memory import DialogueMemory
from jarvis.ollama_stream import stream_project
from jarvis.ollama_dialogue import OllamaError
from jarvis.projects import Projects


class OllamaStreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "test.db")
        db = Projects(self.path)
        self.pid = db.add("JARVIS")
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_stream_persists_complete_answer(self):
        captured = {}

        def fake_transport(req, timeout):
            captured.update(json.loads(req.data))
            return io.BytesIO(
                b'{"message":{"content":"Hello "},"done":false}\n'
                b'{"message":{"content":"world"},"done":false}\n'
                b'{"done":true}\n')
        gen = stream_project(self.pid, "Question", db_path=self.path,
                             transport=fake_transport)
        self.assertEqual(list(gen), ["Hello ", "world"])
        self.assertTrue(captured["stream"])
        memory = DialogueMemory(self.path)
        try:
            self.assertEqual(memory.recent(self.pid)[-1]["content"], "Hello world")
        finally:
            memory.close()

    def test_incomplete_stream_does_not_persist(self):
        def fake_transport(req, timeout):
            return io.BytesIO(b'{"message":{"content":"partial"}}\n')
        with self.assertRaises(OllamaError):
            list(stream_project(self.pid, "Question", db_path=self.path,
                                transport=fake_transport))
        memory = DialogueMemory(self.path)
        try:
            self.assertEqual(memory.recent(self.pid), [])
        finally:
            memory.close()


if __name__ == "__main__":
    unittest.main()
