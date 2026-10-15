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

    def test_review_requires_academy_confirmation_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "jarvis.db")
            from jarvis.academy import Academy
            academy = Academy(path)
            from jarvis.learning_director import LearningDirector
            director = LearningDirector(path)
            goal_id = director.add_goal("programming", "Python documentation")
            audit = LearningAudit(path)
            url = "https://docs.python.org/3/"
            audit.record(goal_id, "pending_review", url)
            with self.assertRaises(ValueError):
                audit.confirm_review(goal_id, url)
            academy.db.execute(
                "INSERT INTO academy_sources(url,skill,title,excerpt,fetched_at,reviewed) VALUES(?,?,?,?,?,1)",
                (url, "python", "Python", "Verified", "2026-10-15T00:00:00Z"))
            academy.db.commit()
            self.assertTrue(audit.confirm_review(1, url))
            self.assertFalse(audit.confirm_review(1, url))
            self.assertEqual([r["outcome"] for r in audit.recent()].count("reviewed"), 1)
            self.assertEqual(director.next_goals()[0]["completed_sessions"], 1)
            audit.close()
            director.close()
            academy.close()

    def test_invalid_outcomes_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            audit = LearningAudit(str(Path(folder) / "jarvis.db"))
            with self.assertRaises(ValueError):
                audit.record(1, "mastered")
            audit.close()


if __name__ == "__main__":
    unittest.main()
