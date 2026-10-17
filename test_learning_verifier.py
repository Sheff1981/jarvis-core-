import tempfile
import unittest
from pathlib import Path
from jarvis.learning import LearningJournal
from jarvis.learning_verifier import audit, validate_source

class SourceAuditTests(unittest.TestCase):
    def test_allowlist(self):
        self.assertTrue(validate_source("https://github.com/python/cpython/releases/tag/v3.14"))
        self.assertFalse(validate_source("https://github.com/attacker/release"))
        self.assertFalse(validate_source("https://github.com.evil.test/python/cpython/releases/x"))
        self.assertFalse(validate_source("http://github.com/python/cpython/releases/x"))

    def test_audit_is_idempotent_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "learning.db")
            journal = LearningJournal(path)
            journal.record("rss", "Python release", "collected", {"url": "https://github.com/python/cpython/releases/tag/v3"})
            journal.record("rss", "Unknown", "collected", {"url": "https://example.com/x"})
            self.assertEqual(audit(path), {"source_accepted": 1, "source_rejected": 1})
            self.assertEqual(audit(path), {"source_accepted": 0, "source_rejected": 0})
            events = journal.daily_report()["events"]
            self.assertEqual(events[0]["status"], "collected")
            self.assertEqual(events[1]["status"], "collected")
            self.assertEqual([e["status"] for e in events[2:]], ["verified", "failed"])
            self.assertTrue(all(e["evidence"]["scope"] == "source_provenance_only" for e in events[2:]))
