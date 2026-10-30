"""Tests for dialogue history persistence and isolation."""
import os
import tempfile
import unittest
from jarvis.dialogue_memory import DialogueMemory


class DialogueMemoryTests(unittest.TestCase):
    def test_persistence_order_and_project_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            db = DialogueMemory(path)
            db.append("jarvis", "user", "What next?")
            db.append("other", "user", "Private other project")
            db.append("jarvis", "assistant", "Run tests")
            db.close()
            db = DialogueMemory(path)
            try:
                history = db.recent("jarvis")
                self.assertEqual([x["content"] for x in history], ["What next?", "Run tests"])
                self.assertEqual([x["role"] for x in history], ["user", "assistant"])
                self.assertEqual(len(db.recent("jarvis", limit=1)), 1)
                self.assertEqual(db.recent("missing"), [])
            finally:
                db.close()

    def test_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            db = DialogueMemory(os.path.join(directory, "memory.db"))
            try:
                for args in [("", "user", "text"), ("x", "system", "text"), ("x", "user", "  ")]:
                    with self.assertRaises(ValueError):
                        db.append(*args)
                for limit in (0, -1, 101, True, "5"):
                    with self.assertRaises(ValueError):
                        db.recent("x", limit)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
