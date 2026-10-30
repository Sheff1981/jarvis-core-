import tempfile
import unittest
from pathlib import Path

from jarvis.windows_actions import WindowsActions


class WindowsActionTests(unittest.TestCase):
    def test_directory_listing_requires_exact_one_time_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "hello.txt").write_text("hello", encoding="utf-8")
            actions = WindowsActions()
            request = actions.propose("list_directory", folder)
            with self.assertRaises(PermissionError):
                actions.execute(request.token, "list_directory", folder)
            self.assertTrue(actions.gate.approve(request.token))
            self.assertEqual(actions.execute(request.token, "list_directory", folder),
                             ["hello.txt"])
            with self.assertRaises(PermissionError):
                actions.execute(request.token, "list_directory", folder)

    def test_file_metadata_and_operation_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "hello.txt"
            file.write_text("hello", encoding="utf-8")
            actions = WindowsActions()
            request = actions.propose("file_info", str(file))
            actions.gate.approve(request.token)
            with self.assertRaises(PermissionError):
                actions.execute(request.token, "list_directory", str(file))
            with self.assertRaises(PermissionError):
                actions.execute(request.token, "file_info", str(file))
            second = actions.propose("file_info", str(file))
            actions.gate.approve(second.token)
            result = actions.execute(second.token, "file_info", str(file))
            self.assertEqual(result["size"], 5)
            self.assertEqual(actions.audit[-1]["status"], "success")

    def test_mutating_operations_cannot_be_proposed(self):
        actions = WindowsActions()
        for operation in ("delete", "write", "run", "shell"):
            with self.assertRaises(ValueError):
                actions.propose(operation, ".")


if __name__ == "__main__":
    unittest.main()
