"""Non-destructive migration from the original projects schema."""
import os
import sqlite3
import tempfile
import unittest
from jarvis.projects import Projects


class LegacyMigrationTests(unittest.TestCase):
    def test_original_schema_survives_migration_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "legacy.db")
            with sqlite3.connect(path) as db:
                db.execute("""CREATE TABLE projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    next_step TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL)""")
                db.execute("INSERT INTO projects VALUES (?,?,?,?,?)",
                           ("legacy-id", "Existing", "active", "old step", "2026-01-01"))
            store = Projects(path)
            self.assertEqual(store.list()[0]["next_step"], "old step")
            self.assertIsNone(store.latest_checkpoint("legacy-id"))
            store.checkpoint("legacy-id", stage="Migration", task="Verify",
                             status="done", next_step="ready")
            store.close()
            reopened = Projects(path)
            self.assertEqual(reopened.latest_checkpoint("legacy-id")["task"], "Verify")
            self.assertEqual(reopened.list()[0]["id"], "legacy-id")
            reopened.close()

    def test_repeated_initialization_preserves_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "reopen.db")
            first = Projects(path)
            pid = first.add("Existing", "next")
            first.close()
            for _ in range(3):
                store = Projects(path)
                self.assertEqual(store.list()[0]["id"], pid)
                store.close()


if __name__ == "__main__":
    unittest.main()
