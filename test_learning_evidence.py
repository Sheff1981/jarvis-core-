import tempfile
import unittest
from pathlib import Path
from jarvis.learning import LearningJournal
from jarvis.learning_evidence import add_evidence, pending_evidence

class EvidenceTests(unittest.TestCase):
    def test_pending_and_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "journal.db")
            source = LearningJournal(db).record("rss", "Python release", "collected",
                                                 {"url": "https://www.python.org/"})
            first = add_evidence(db, source, "A release exists", "Release notes",
                                 "https://www.python.org/downloads/")
            second = add_evidence(db, source, "A release exists", "Release notes",
                                  "https://www.python.org/downloads/")
            self.assertEqual(first, second)
            rows = pending_evidence(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["review_status"], "pending")

    def test_reject_missing_source_and_http(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "journal.db")
            LearningJournal(db)
            with self.assertRaises(ValueError):
                add_evidence(db, 999, "Claim", "Excerpt", "https://www.python.org/")
            with self.assertRaises(ValueError):
                add_evidence(db, 999, "Claim", "Excerpt", "http://www.python.org/")
