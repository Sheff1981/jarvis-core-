"""Offline CLI tests; no Ollama installation needed."""
import os
import tempfile
import unittest

from jarvis.projects import Projects
from dialogue_cli import main


class DialogueCliTests(unittest.TestCase):
    def test_one_turn_and_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "jarvis.db")
            db = Projects(path)
            project_id = db.add("JARVIS")
            db.close()
            lines = iter(["Привет", "/exit"])
            outputs = []
            calls = []

            def fake_ask(pid, question, **kwargs):
                calls.append((pid, question, kwargs))
                return "Здравствуйте"

            status = main([project_id, "--db", path], input_fn=lambda _: next(lines),
                          output_fn=outputs.append, ask_fn=fake_ask)
            self.assertEqual(status, 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1], "Привет")
            self.assertIn("JARVIS: Здравствуйте", outputs)

    def test_unknown_project(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "jarvis.db")
            outputs = []
            status = main(["missing", "--db", path], output_fn=outputs.append)
            self.assertEqual(status, 2)
            self.assertIn("Project not found", outputs[0])


if __name__ == "__main__":
    unittest.main()
