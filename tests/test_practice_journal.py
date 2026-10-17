"""Tests for Academy practical exercises and evidence requirements."""
import tempfile
import unittest
from pathlib import Path
from jarvis.practice_journal import PracticeJournal


class PracticeJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.journal = PracticeJournal(str(Path(self.temp.name) / "practice.db"))

    def tearDown(self):
        self.journal.close()
        self.temp.cleanup()

    def test_proposals_are_not_skills(self):
        exercise = self.journal.propose("Rust", "Parse data", "Parse a bounded JSON document")
        self.assertGreater(exercise, 0)
        self.assertEqual(self.journal.summary()["Rust"], {"proposed": 1})

    def test_evidence_requires_trusted_runner(self):
        exercise = self.journal.propose("Java", "Calculator", "Add integers")
        report = {"runner": "isolated-ci", "test_count": 4}
        with self.assertRaises(PermissionError):
            self.journal.record_external_test(exercise, "class Main {}", report, passed=True)
        digest = self.journal.record_external_test(
            exercise, "class Main {}", report, passed=True, trusted_runner=True)
        self.assertEqual(len(digest), 64)
        self.assertEqual(self.journal.summary()["Java"], {"passed": 1})

    def test_invalid_reports_rejected(self):
        exercise = self.journal.propose("Python", "Example", "Return a value")
        with self.assertRaises(ValueError):
            self.journal.record_external_test(
                exercise, "print(1)", {}, passed=True, trusted_runner=True)
        self.assertEqual(self.journal.summary()["Python"], {"proposed": 1})


if __name__ == "__main__":
    unittest.main()
