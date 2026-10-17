"""Check the actual Ollama request respects laptop resource limits."""
import io
import json
import os
import tempfile
import unittest

from jarvis.dialogue_memory import DialogueMemory
from jarvis.inference_profile import InferenceProfile
from jarvis.ollama_dialogue import ask_project
from jarvis.projects import Projects


class CpuIntegrationTests(unittest.TestCase):
    def test_bounded_history_and_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = os.path.join(folder, "jarvis.db")
            projects = Projects(db_path)
            project_id = projects.add("JARVIS")
            projects.close()
            memory = DialogueMemory(db_path)
            for i in range(12):
                memory.append(project_id, "user", "turn " + str(i))
            memory.close()
            captured = {}

            def fake_transport(req, timeout):
                captured.update(json.loads(req.data.decode("utf-8")))
                return io.BytesIO(b'{"message":{"content":"ok"}}')

            profile = InferenceProfile(history_limit=4, num_predict=80, num_ctx=1024)
            self.assertEqual(
                ask_project(project_id, "next", db_path=db_path,
                            transport=fake_transport, profile=profile), "ok")
            self.assertEqual(captured["model"], "qwen2.5:1.5b")
            self.assertEqual(captured["options"]["num_predict"], 80)
            self.assertEqual(captured["options"]["num_ctx"], 1024)
            self.assertEqual(len(captured["messages"]), 6)
            self.assertEqual(captured["messages"][-1]["content"], "next")


if __name__ == "__main__":
    unittest.main()
