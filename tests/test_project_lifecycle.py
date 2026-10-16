"""Project export and explicit deletion regression tests."""
import json
import os
import tempfile
import unittest
from jarvis.projects import Projects
from jarvis.conversation_memory import ConversationMemory


class ProjectLifecycleTests(unittest.TestCase):
    def test_export_and_confirmed_delete_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            store = Projects(path)
            first = store.add("First")
            second = store.add("Second", "untouched")
            store.checkpoint(first, stage="Memory", task="Export",
                             status="done", evidence="unit test")
            store.record_decision(first, "Keep history")
            store.queue_idea(first, "Later")
            memory = ConversationMemory(path)
            memory.append("user", "preserve conversation")
            payload = json.loads(store.export_project(first))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["checkpoints"][0]["stage"], "Memory")
            self.assertEqual(len(payload["decisions"]), 1)
            self.assertEqual(len(payload["ideas"]), 1)
            self.assertNotIn("preserve conversation", json.dumps(payload))
            with self.assertRaises(PermissionError):
                store.delete_project(first)
            store.delete_project(first, confirm=True)
            with self.assertRaises(KeyError):
                store.export_project(first)
            self.assertEqual(store.list()[0]["id"], second)
            self.assertEqual(memory.recent()[0]["content"], "preserve conversation")
            memory.close()
            store.close()


if __name__ == "__main__":
    unittest.main()
