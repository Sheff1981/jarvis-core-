import tempfile
import unittest
from pathlib import Path
from jarvis.private_session_journal import PrivateSessionJournal


class PrivateSessionJournalTests(unittest.TestCase):
    def test_opt_in_isolation_and_forgetting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.db"
            journal = PrivateSessionJournal(path)
            with self.assertRaises(PermissionError):
                journal.append("owner", "user", "Привет")
            journal.append("owner", "user", "Привет", consent=True)
            journal.append("owner", "assistant", "Здравствуйте", consent=True)
            journal.append("other", "user", "Секрет", consent=True)
            self.assertEqual(len(PrivateSessionJournal(path).recent("owner")), 2)
            self.assertEqual(len(journal.recent("other")), 1)
            self.assertEqual(journal.forget("owner"), 2)
            self.assertEqual(journal.recent("owner"), [])
            self.assertEqual(len(journal.recent("other")), 1)

    def test_invalid_role(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = PrivateSessionJournal(Path(directory) / "private.db")
            with self.assertRaises(ValueError):
                journal.append("owner", "system", "hidden", consent=True)


if __name__ == "__main__":
    unittest.main()
