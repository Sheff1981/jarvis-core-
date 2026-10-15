"""Offline checks for background voice logging and launch lifetime."""
import contextlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis import background


class BackgroundTests(unittest.TestCase):
    def test_redirects_output_and_passes_voice_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "logs" / "voice.log"
            observed = []
            fake = types.ModuleType("voice_chat")
            fake.__file__ = "voice_chat.py"
            def main():
                observed.append(sys.argv[:])
                print("voice test running", flush=True)
            fake.main = main
            with patch.dict(sys.modules, {"voice_chat": fake}):
                result = background.run(["--cpu-only", "--tray"], log_file=log)
            self.assertEqual(result, 0)
            self.assertEqual(observed, [["voice_chat.py", "--cpu-only", "--tray"]])
            self.assertIn("voice test running", log.read_text("utf-8"))

    def test_second_instance_is_refused(self):
        @contextlib.contextmanager
        def already_running():
            yield False
        with tempfile.TemporaryDirectory() as tmp:
            with patch("jarvis.background.single_instance", already_running):
                result = background.run([], log_file=Path(tmp) / "voice.log")
            self.assertEqual(result, 0)
            self.assertIn("second instance refused", (Path(tmp) / "voice.log").read_text("utf-8"))

    def test_errors_are_logged_without_crashing_pythonw(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "voice.log"
            fake = types.ModuleType("voice_chat")
            fake.__file__ = "voice_chat.py"
            def main():
                raise ValueError("simulated startup error")
            fake.main = main
            with patch.dict(sys.modules, {"voice_chat": fake}):
                result = background.run([], log_file=log)
            self.assertEqual(result, 1)
            self.assertIn("simulated startup error", log.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
