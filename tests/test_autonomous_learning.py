"""Autonomous learning must respect offline, opt-in and verification boundaries."""
import tempfile
import unittest
from pathlib import Path
from jarvis.autonomous_learning import AutonomousLearningLoop
from jarvis.learning_director import LearningDirector
from jarvis.research_agent import ResearchResult


class FakeResearcher:
    def __init__(self, academy):
        self.academy = academy

    def study(self, url, skill):
        return ResearchResult(url, "direct", "pending_review", 100)


class AutonomousLearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "brain.db")
        director = LearningDirector(self.db)
        self.goal = director.add_goal("programming", "Python", 5)
        director.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_disabled_and_offline_are_safe(self):
        loop = AutonomousLearningLoop(self.db, online_probe=lambda: False)
        self.assertEqual(loop.tick()["status"], "disabled")
        self.assertEqual(loop.tick(enabled=True)["status"], "offline")

    def test_online_studies_but_does_not_claim_proficiency(self):
        loop = AutonomousLearningLoop(
            self.db, online_probe=lambda: True, researcher_factory=FakeResearcher)
        result = loop.tick(enabled=True)
        self.assertEqual(result["pages"], 1)
        self.assertEqual(result["results"][0]["status"], "pending_review")
        director = LearningDirector(self.db)
        self.assertEqual(director.next_goals()[0]["completed_sessions"], 0)
        director.close()

    def test_unexpected_research_status_is_not_marked_pending(self):
        class UnexpectedResearcher:
            def __init__(self, academy):
                pass

            def study(self, url, skill):
                return ResearchResult(url, "direct", "mastered", 100)

        from jarvis.learning_audit import LearningAudit
        loop = AutonomousLearningLoop(
            self.db, online_probe=lambda: True, researcher_factory=UnexpectedResearcher)
        result = loop.tick(enabled=True)
        self.assertEqual(result["results"][0]["status"], "error")
        audit = LearningAudit(self.db)
        self.assertEqual(audit.recent()[0]["outcome"], "error")
        audit.close()

    def test_invalid_budget_rejected(self):
        loop = AutonomousLearningLoop(self.db, online_probe=lambda: True)
        with self.assertRaises(ValueError):
            loop.tick(enabled=True, max_pages=50)


if __name__ == "__main__":
    unittest.main()
