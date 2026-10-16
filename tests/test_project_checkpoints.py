"""Regression tests for durable project checkpoints."""
import os
import tempfile
import unittest

from jarvis.projects import Projects
from jarvis.conversation_memory import ConversationMemory


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

    def test_backup_restore_shared_sqlite_and_legacy_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "source.db")
            backup = os.path.join(tmp, "backup.db")
            store = Projects(path)
            project_id = store.add("Project", "old step")
            memory = ConversationMemory(path)
            memory.append("user", "Remember this")
            memory.close()
            store.checkpoint(project_id, stage="Stage", task="Task",
                             status="done", evidence="confirmed", next_step="next")
            store.backup(backup)
            store.close()
            restored = Projects(backup)
            self.assertEqual(restored.latest_checkpoint(project_id)["evidence"], "confirmed")
            self.assertEqual(restored.list()[0]["next_step"], "next")
            history = ConversationMemory(backup)
            self.assertEqual(history.recent()[0]["content"], "Remember this")
            history.close()
            restored.close()

    def test_explicit_restore_to_new_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "source.db")
            backup = os.path.join(tmp, "backup.db")
            target = os.path.join(tmp, "restored.db")
            store = Projects(source)
            project_id = store.add("Restore target", "resume")
            store.checkpoint(project_id, stage="Memory", task="Restore",
                             status="done", next_step="continue")
            store.backup(backup)
            store.close()
            Projects.restore_backup(backup, target)
            restored = Projects(target)
            self.assertEqual(restored.list()[0]["name"], "Restore target")
            self.assertEqual(restored.latest_checkpoint(project_id)["next_step"], "continue")
            restored.close()
            with self.assertRaises(ValueError):
                Projects.restore_backup(backup, target)
            with self.assertRaises(ValueError):
                Projects.restore_backup(os.path.join(tmp, "missing.db"),
                                        os.path.join(tmp, "other.db"))

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
