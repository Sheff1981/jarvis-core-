import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.action_dialogue import ActionDialogue
from jarvis.windows_actions import WindowsActions


class ExplorerActionTests(unittest.TestCase):
    def test_windows_explorer_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            actions = WindowsActions()
            dialogue = ActionDialogue(actions)
            with patch("jarvis.windows_actions.os.name", "nt"), patch(
                "jarvis.windows_actions.os.startfile", create=True
            ) as startfile:
                prompt = dialogue.respond("джарвис открой папку " + folder)
                self.assertIn("Разрешаешь", prompt)
                startfile.assert_not_called()
                answer = dialogue.respond("разрешаю")
                self.assertIn("Открываю", answer)
                startfile.assert_called_once()
                self.assertEqual(Path(startfile.call_args.args[0]), Path(folder).resolve())

    def test_refusal_does_not_open_explorer(self):
        with tempfile.TemporaryDirectory() as folder:
            dialogue = ActionDialogue()
            with patch("jarvis.windows_actions.os.startfile", create=True) as startfile:
                dialogue.respond("открой папку " + folder)
                self.assertIn("отменено", dialogue.respond("нет"))
                startfile.assert_not_called()

    def test_drive_c_command_is_normalized(self):
        dialogue = ActionDialogue()
        dialogue.respond("Джарвис, открой мне диск С")
        self.assertEqual(dialogue.pending.operation, "open_explorer")
        self.assertIn("C:", dialogue.pending.target.upper())
        dialogue.close()


if __name__ == "__main__":
    unittest.main()
