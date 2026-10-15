"""Offline regression tests for current-user Windows voice autostart."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.startup import (
    STARTUP_NAME, LEGACY_STARTUP_NAME, install, startup_script,
    uninstall, startup_folder,
)


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.python = self.root / "python.exe"
        self.pythonw = self.root / "pythonw.exe"
        self.entry = self.root / "source" / "voice_chat.py"
        self.model = self.root / "model"
        self.db = self.root / "memory.db"
        self.piper = self.root / "piper.exe"
        self.ruslan = self.root / "ruslan.onnx"
        self.entry.parent.mkdir()
        self.model.mkdir()
        for file in (self.python, self.pythonw, self.entry, self.piper, self.ruslan):
            file.touch()

    def script(self):
        return startup_script(
            self.python, self.entry, self.model, self.db,
            piper_bin=self.piper, piper_voice=self.ruslan,
        )

    @patch("jarvis.startup.sys.platform", "win32")
    def test_opt_in_install_and_remove(self):
        folder = startup_folder(self.root)
        self.assertFalse(folder.exists())
        target = install(self.script(), self.root)
        self.assertEqual(target.name, STARTUP_NAME)
        self.assertTrue(target.exists())
        self.assertIn("jarvis.background", target.read_text(encoding="utf-8"))
        with self.assertRaises(FileExistsError):
            install(self.script(), self.root)
        self.assertTrue(uninstall(self.root))
        self.assertFalse(uninstall(self.root))

    @patch("jarvis.startup.sys.platform", "win32")
    def test_does_not_remove_modified_entry(self):
        folder = startup_folder(self.root)
        folder.mkdir(parents=True)
        target = folder / STARTUP_NAME
        target.write_text("other application", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            uninstall(self.root)
        self.assertTrue(target.exists())

    def test_script_uses_absolute_paths_and_real_voice_flags(self):
        script = self.script()
        for expected in ("pythonw.exe", "jarvis.background", "--cpu-only",
                         "--tray", "--diagnostics", "--speak", "--tts",
                         "piper", "--piper-voice", "--piper-bin",
                         "qwen2.5:3b-instruct-q6_K", str(self.model.resolve()),
                         str(self.db.resolve())):
            self.assertIn(expected, script)
        self.assertNotIn("--require-wake-word", script)
        self.assertNotIn("--always-listen", script)
        self.assertIn('shell.CurrentDirectory', script)

    def test_rejects_unsafe_model_name(self):
        with self.assertRaises(ValueError):
            startup_script(self.python, self.entry, self.model, self.db, "model&calc")

    def test_rejects_missing_pythonw_and_invalid_piper(self):
        self.pythonw.unlink()
        with self.assertRaisesRegex(ValueError, "pythonw"):
            self.script()
        self.pythonw.touch()
        with self.assertRaises(ValueError):
            startup_script(self.python, self.entry, self.model, self.db,
                           piper_bin=self.piper)
        with self.assertRaises(ValueError):
            startup_script(self.python, self.entry, self.model, self.db,
                           piper_bin=self.piper, piper_voice=self.ruslan,
                           piper_length_scale=float("nan"))

    @patch("jarvis.startup.sys.platform", "win32")
    def test_legacy_script_never_overwritten(self):
        folder = startup_folder(self.root)
        folder.mkdir(parents=True)
        legacy = folder / LEGACY_STARTUP_NAME
        legacy.write_text("foreign entry", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            install(self.script(), self.root)
        self.assertEqual(legacy.read_text("utf-8"), "foreign entry")

    @patch("jarvis.startup.sys.platform", "win32")
    def test_memory_is_not_modified_by_install_or_remove(self):
        self.db.write_text("preserve database", encoding="utf-8")
        install(self.script(), self.root)
        uninstall(self.root)
        self.assertEqual(self.db.read_text("utf-8"), "preserve database")


if __name__ == "__main__":
    unittest.main()
