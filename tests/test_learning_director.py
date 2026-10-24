"""Learning director prioritization, persistence and evidence tests."""
import tempfile
import unittest
from pathlib import Path
from jarvis.learning_director import LearningDirector


class LearningDirectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "learning.db")
        self.director = LearningDirector(self.path)

    def tearDown(self):
        self.director.close()
        self.temp.cleanup()

    def test_cross_domain_priorities_and_persistence(self):
        self.director.add_goal("history", "Ancient Rome", 2)
        goal = self.director.add_goal("programming", "Java and C++", 5)
        self.assertEqual(self.director.next_goals()[0]["id"], goal)
        self.director.record_session(goal, sources_reviewed=1)
        self.director.close()
        self.director = LearningDirector(self.path)
        self.assertEqual(self.director.next_goals()[0]["completed_sessions"], 1)

    def test_no_false_learning_without_evidence(self):
        goal = self.director.add_goal("psychology", "Empathetic communication")
        with self.assertRaises(ValueError):
            self.director.record_session(goal)
        self.assertEqual(self.director.next_goals()[0]["completed_sessions"], 0)

    def test_pause_blocks_learning(self):
        goal = self.director.add_goal("philosophy", "Logic")
        self.director.pause(goal)
        self.assertEqual(self.director.next_goals(), [])
        with self.assertRaises(ValueError):
            self.director.record_session(goal, exercises_passed=1)

    def test_invalid_domains_rejected(self):
        with self.assertRaises(ValueError):
            self.director.add_goal("unknown", "topic")


if __name__ == "__main__":
    unittest.main()
