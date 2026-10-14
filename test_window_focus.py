import unittest
from unittest.mock import patch
from jarvis.action_dialogue import ActionDialogue


class WindowFocusTests(unittest.TestCase):
    def test_focus_requires_approval(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.focus_window_exact", return_value={"focused": "Notes"}) as focus:
            self.assertIn("Разрешаешь", dialogue.respond("переключись на окно Notes"))
            focus.assert_not_called()
            self.assertIn("Notes", dialogue.respond("разрешаю"))
            focus.assert_called_once_with("Notes")

    def test_refusal_prevents_focus(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.focus_window_exact") as focus:
            dialogue.respond("активируй окно Notes")
            dialogue.respond("нет")
            focus.assert_not_called()


if __name__ == "__main__":
    unittest.main()
