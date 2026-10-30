"""Regression tests for persistent project memory."""
import os
import tempfile
import unittest

from jarvis.projects import Projects


class ProjectMemoryRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "projects.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_persistence_and_completion_filter(self):
        db = Projects(self.path)
        try:
            project_id = db.add("JARVIS", "Check dialogue context")
            db.update(project_id, next_step="Run regression tests")
        finally:
            db.close()
        reopened = Projects(self.path)
        try:
            entries = reopened.list()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["id"], project_id)
            self.assertEqual(entries[0]["next_step"], "Run regression tests")
            reopened.update(project_id, status="done")
            self.assertEqual(reopened.list(), [])
            self.assertEqual(len(reopened.list(include_done=True)), 1)
        finally:
            reopened.close()

    def test_reject_invalid_status_and_missing_project(self):
        db = Projects(self.path)
        try:
            project_id = db.add("Memory")
            with self.assertRaises(ValueError):
                db.update(project_id, status="deleted")
            with self.assertRaises(ValueError):
                db.update(project_id)
            with self.assertRaises(KeyError):
                db.update("missing-id", status="done")
            self.assertEqual(db.list()[0]["status"], "active")
        finally:
            db.close()

    def test_empty_project_name_rejected(self):
        db = Projects(self.path)
        try:
            with self.assertRaises(ValueError):
                db.add("   ")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
