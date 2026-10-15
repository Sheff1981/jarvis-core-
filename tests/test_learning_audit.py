"""Persistent research audit must not grant learning credit."""
import tempfile
import unittest
from pathlib import Path
from jarvis.learning_audit import LearningAudit


class LearningAuditTests(unittest.TestCase):
    def test_persists_across_restarts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "jarvis.db")
            audit = LearningAudit(path)
            audit.record(7, "pending_review", "https://docs.python.org/3/")
            audit.close()
            audit = LearningAudit(path)
            self.assertEqual(audit.recent()[0]["goal_id"], 7)
            self.assertEqual(audit.recent()[0]["outcome"], "pending_review")
            audit.close()

    def test_invalid_outcomes_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            audit = LearningAudit(str(Path(folder) / "jarvis.db"))
            with self.assertRaises(ValueError):
                audit.record(1, "mastered")
            audit.close()


if __name__ == "__main__":
    unittest.main()
