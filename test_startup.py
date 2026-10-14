import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from jarvis.startup import install, startup_script, uninstall, startup_folder, STARTUP_NAME


class StartupTests(unittest.TestCase):
    def test_opt_in_install_and_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("jarvis.startup.sys.platform", "win32"):
                folder = startup_folder(tmp)
                self.assertFalse(folder.exists())
                target = install("voice_chat.py --require-wake-word --speak\n", tmp)
                self.assertEqual(target.name, STARTUP_NAME)
                self.assertTrue(target.exists())
                with self.assertRaises(FileExistsError):
                    install("anything", tmp)
                self.assertTrue(uninstall(tmp))
                self.assertFalse(uninstall(tmp))

    def test_does_not_remove_modified_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("jarvis.startup.sys.platform", "win32"):
                target = install("other application", tmp)
                with self.assertRaises(RuntimeError):
                    uninstall(tmp)
                self.assertTrue(target.exists())

    def test_script_uses_absolute_paths_and_wake_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, entry, model = root / "python.exe", root / "voice_chat.py", root / "model"
            exe.touch()
            entry.touch()
            model.mkdir()
            script = startup_script(exe, entry, model, root / "jarvis.db")
            self.assertIn("--require-wake-word --speak", script)
            self.assertIn(str(entry.resolve()), script)
            self.assertIn("--db", script)

    def test_rejects_unsafe_model_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, entry, model = root / "python.exe", root / "voice_chat.py", root / "model"
            exe.touch()
            entry.touch()
            model.mkdir()
            with self.assertRaises(ValueError):
                startup_script(exe, entry, model, root / "db", "model&calc")


if __name__ == "__main__":
    unittest.main()
