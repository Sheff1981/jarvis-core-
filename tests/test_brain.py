"""Local brain regression tests."""
import os
import tempfile
import unittest
from jarvis.brain import Brain


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "brain.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_memory_survives_restart_and_scopes_are_isolated(self):
        brain = Brain(self.path)
        brain.remember("project-a", "goal", "Make JARVIS local")
        brain.remember("project-b", "goal", "Other")
        brain.close()
        brain = Brain(self.path)
        self.assertEqual(brain.recall("project-a"), {"goal": "Make JARVIS local"})
        self.assertEqual(brain.recall("project-b"), {"goal": "Other"})
        brain.remember("project-a", "goal", "Updated")
        self.assertEqual(brain.recall("project-a")["goal"], "Updated")
        brain.close()

    def test_task_needs_explicit_approval(self):
        brain = Brain(self.path)
        task_id = brain.propose("jarvis", "Check voice engine")
        self.assertEqual(brain.tasks("jarvis")[0]["state"], "proposed")
        brain.approve(task_id)
        self.assertEqual(brain.tasks("jarvis")[0]["state"], "approved")
        with self.assertRaises(ValueError):
            brain.approve(task_id)
        brain.close()

    def test_rejects_empty_memory(self):
        brain = Brain(self.path)
        with self.assertRaises(ValueError):
            brain.remember("jarvis", "", "x")
        brain.close()


if __name__ == "__main__":
    unittest.main()
