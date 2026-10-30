"""Project decision and deferred idea queue regression tests."""
import os
import tempfile
import unittest
from jarvis.projects import Projects


class DecisionQueueTests(unittest.TestCase):
    def test_decisions_ideas_restart_without_changing_active_task(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            store = Projects(path)
            pid = store.add("JARVIS", "Finish Memory Core")
            store.record_decision(pid, "Keep one database", rationale="Compatibility",
                                  evidence="schema audit")
            idea_id = store.queue_idea(pid, "Build mobile UI later")
            self.assertEqual(store.list()[0]["next_step"], "Finish Memory Core")
            store.close()
            restored = Projects(path)
            self.assertEqual(restored.decisions(pid)[0]["evidence"], "schema audit")
            self.assertEqual(restored.ideas(pid)[0]["status"], "queued")
            restored.resolve_idea(pid, idea_id, "accepted")
            self.assertEqual(restored.ideas(pid)[0]["status"], "accepted")
            self.assertEqual(restored.list()[0]["next_step"], "Finish Memory Core")
            restored.close()

    def test_validation_and_project_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Projects(os.path.join(directory, "memory.db"))
            first = store.add("One")
            second = store.add("Two")
            idea_id = store.queue_idea(first, "Later")
            with self.assertRaises(ValueError):
                store.resolve_idea(second, idea_id, "accepted")
            with self.assertRaises(ValueError):
                store.record_decision(first, "")
            with self.assertRaises(KeyError):
                store.queue_idea("missing", "Idea")
            store.close()


if __name__ == "__main__":
    unittest.main()
