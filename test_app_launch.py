import unittest
from unittest.mock import patch

from jarvis.action_dialogue import ActionDialogue
from jarvis.windows_actions import WindowsActions


class ApplicationLaunchTests(unittest.TestCase):
    def test_notepad_requires_approval(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.os.name", "nt"), patch(
            "jarvis.windows_actions.subprocess.Popen"
        ) as launch:
            self.assertIn("Разрешаешь", dialogue.respond("Джарвис, открой блокнот"))
            launch.assert_not_called()
            self.assertIn("Запускаю", dialogue.respond("разрешаю"))
            launch.assert_called_once_with(["notepad.exe"], shell=False)

    def test_denial_prevents_launch(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.subprocess.Popen") as launch:
            dialogue.respond("запусти калькулятор")
            self.assertIn("отменено", dialogue.respond("нет"))
            launch.assert_not_called()

    def test_unknown_app_is_not_executable(self):
        actions = WindowsActions()
        with self.assertRaises(ValueError):
            actions.propose("open_app", "powershell")
        with self.assertRaises(ValueError):
            actions.propose("open_app", "C:/malware.exe")


if __name__ == "__main__":
    unittest.main()
