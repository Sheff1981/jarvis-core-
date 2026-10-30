import tempfile
import unittest
from pathlib import Path
from jarvis.learning import LearningJournal


class LearningJournalTests(unittest.TestCase):
    def test_persistence_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learning.db"
            journal = LearningJournal(path)
            journal.record("python", "SQLite test", "verified", {"test": "passed"})
            report = LearningJournal(path).daily_report()
            self.assertEqual(report["verified"], 1)
            self.assertEqual(report["events"][0]["evidence"]["test"], "passed")

    def test_verified_requires_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = LearningJournal(Path(directory) / "learning.db")
            with self.assertRaises(ValueError):
                journal.record("python", "Unverified claim", "verified")


if __name__ == "__main__":
    unittest.main()
