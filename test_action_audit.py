import tempfile
import unittest
from pathlib import Path
from jarvis.action_audit import ActionAudit
from jarvis.windows_actions import WindowsActions


class AuditTests(unittest.TestCase):
    def test_persists_success_after_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "audit.db"
            store = ActionAudit(db)
            actions = WindowsActions(audit_store=store)
            request = actions.propose("list_directory", folder)
            actions.gate.approve(request.token)
            actions.execute(request.token, "list_directory", folder)
            store.close()
            reopened = ActionAudit(db)
            try:
                events = reopened.recent()
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["operation"], "list_directory")
                self.assertEqual(events[0]["status"], "success")
                self.assertNotIn("token", events[0])
            finally:
                reopened.close()

    def test_failed_operation_is_logged(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ActionAudit(Path(folder) / "audit.db")
            try:
                actions = WindowsActions(audit_store=store)
                missing = str(Path(folder) / "missing")
                request = actions.propose("file_info", missing)
                actions.gate.approve(request.token)
                with self.assertRaises(FileNotFoundError):
                    actions.execute(request.token, "file_info", missing)
                self.assertEqual(store.recent()[0]["status"], "error")
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
