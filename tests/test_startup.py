"""Regression tests for the real Windows voice startup arguments."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.startup import startup_script, install, uninstall, STARTUP_NAME, LEGACY_STARTUP_NAME, startup_folder


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.python = self.root / "python.exe"
        self.pythonw = self.root / "pythonw.exe"
        self.entry = self.root / "core" / "voice_chat.py"
        self.model = self.root / "vosk"
        self.db = self.root / "memory.db"
        self.piper = self.root / "piper.exe"
        self.voice = self.root / "ruslan.onnx"
        self.entry.parent.mkdir()
        self.model.mkdir()
        for item in (self.python, self.pythonw, self.entry, self.piper, self.voice):
            item.write_text("stub", encoding="utf-8")

    def build(self):
        return startup_script(self.python, self.entry, self.model, self.db,
                              piper_bin=self.piper, piper_voice=self.voice)

    def test_hidden_startup_uses_existing_voice_and_no_removed_flag(self):
        script = self.build()
        for expected in ("pythonw.exe", "jarvis.background",
                         "--cpu-only", "--tray", "--diagnostics",
                         "--piper-bin", "--piper-voice", "--tts",
                         "piper", "qwen2.5:3b-instruct-q6_K"):
            self.assertIn(expected, script)
        self.assertNotIn("--require-wake-word", script)
        self.assertNotIn("--always-listen", script)
        self.assertIn(str(self.db), script)
        self.assertIn(str(self.model), script)
        self.assertIn("shell.Run", script)

    def test_required_resources_are_checked(self):
        self.pythonw.unlink()
        with self.assertRaisesRegex(ValueError, "pythonw.exe"):
            self.build()
        self.pythonw.write_text("stub")
        with self.assertRaises(ValueError):
            startup_script(self.python, self.entry, self.model, self.db,
                           piper_bin=self.piper)
        with self.assertRaises(ValueError):
            startup_script(self.python, self.entry, self.model, self.db,
                           piper_bin=self.piper, piper_voice=self.voice,
                           piper_length_scale=float("nan"))

    @patch("jarvis.startup.sys.platform", "win32")
    def test_install_remove_preserves_other_files(self):
        script = self.build()
        self.db.write_text("keep this", encoding="utf-8")
        path = install(script, appdata=self.root)
        self.assertEqual(path.name, STARTUP_NAME)
        self.assertEqual(path.read_text("utf-8"), script)
        with self.assertRaises(FileExistsError):
            install(script, appdata=self.root)
        self.assertTrue(uninstall(appdata=self.root))
        self.assertFalse(uninstall(appdata=self.root))
        self.assertEqual(self.db.read_text("utf-8"), "keep this")

    @patch("jarvis.startup.sys.platform", "win32")
    def test_tampered_startup_entry_is_preserved(self):
        folder = startup_folder(self.root)
        folder.mkdir(parents=True)
        entry = folder / STARTUP_NAME
        entry.write_text("foreign startup", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            uninstall(appdata=self.root)
        self.assertTrue(entry.exists())

    @patch("jarvis.startup.sys.platform", "win32")
    def test_legacy_entry_is_not_overwritten(self):
        folder = startup_folder(self.root)
        folder.mkdir(parents=True)
        legacy = folder / LEGACY_STARTUP_NAME
        legacy.write_text("foreign script", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            install(self.build(), appdata=self.root)
        self.assertTrue(legacy.exists())


if __name__ == "__main__":
    unittest.main()
