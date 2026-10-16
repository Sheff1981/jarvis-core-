"""Regression tests for durable project checkpoints."""
import os
import tempfile
import unittest

from jarvis.projects import Projects


class ProjectCheckpointTests(unittest.TestCase):
    def test_restart_and_existing_project_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "memory.db")
            store = Projects(path)
            project_id = store.add("JARVIS", "audit")
            store.checkpoint(project_id, stage="Memory", task="Persistence",
                             status="running", last_action="audit completed",
                             evidence="test", next_step="restart")
            store.close()
            restored = Projects(path)
            checkpoint = restored.latest_checkpoint(project_id)
            self.assertEqual(checkpoint["stage"], "Memory")
            self.assertEqual(checkpoint["next_step"], "restart")
            self.assertEqual(restored.list()[0]["next_step"], "restart")
            restored.close()

    def test_invalid_and_missing_project_do_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Projects(os.path.join(tmp, "memory.db"))
            project_id = store.add("Existing")
            with self.assertRaises(ValueError):
                store.checkpoint(project_id, stage="x", task="y", status="unknown")
            with self.assertRaises(KeyError):
                store.checkpoint("missing", stage="x", task="y", status="done")
            self.assertIsNone(store.latest_checkpoint(project_id))
            store.close()


if __name__ == "__main__":
    unittest.main()
