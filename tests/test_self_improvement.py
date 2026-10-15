"""Regression tests for guarded source evolution."""
from pathlib import Path
import tempfile
import unittest
from jarvis.self_improvement import SelfImprovement


class SelfImprovementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "jarvis").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "jarvis" / "sample.py").write_text("VALUE = 1\n")
        self.engine = SelfImprovement(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_candidate_does_not_touch_original(self):
        staging = self.engine.stage("jarvis/sample.py", "VALUE = 2\n")
        self.assertEqual((self.root / "jarvis" / "sample.py").read_text(), "VALUE = 1\n")
        with self.assertRaises(PermissionError):
            self.engine.apply(staging, "jarvis/sample.py")
        backup = self.engine.apply(staging, "jarvis/sample.py", validated=True)
        self.assertEqual((self.root / "jarvis" / "sample.py").read_text(), "VALUE = 2\n")
        self.assertEqual(backup.read_text(), "VALUE = 1\n")

    def test_rejects_escape_and_invalid_python(self):
        for path in ("../secret.py", "setup.py", "/tmp/other.py"):
            with self.assertRaises(ValueError):
                self.engine.stage(path, "VALUE = 2\n")
        with self.assertRaises(SyntaxError):
            self.engine.stage("jarvis/sample.py", "def invalid(\n")


if __name__ == "__main__":
    unittest.main()
