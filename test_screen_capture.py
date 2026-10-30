import unittest
from unittest.mock import patch

from jarvis.action_dialogue import ActionDialogue
from jarvis.windows_actions import WindowsActions


class ScreenCaptureTests(unittest.TestCase):
    def test_no_capture_before_approval(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.capture_screen_png", return_value=b"png") as capture:
            self.assertIn("Разрешаешь", dialogue.respond("сделай снимок экрана"))
            capture.assert_not_called()
            self.assertIn("удалён", dialogue.respond("разрешаю"))
            capture.assert_called_once()

    def test_denial_blocks_capture(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.capture_screen_png") as capture:
            dialogue.respond("сделай снимок экрана")
            dialogue.respond("нет")
            capture.assert_not_called()

    def test_unapproved_capture_is_rejected(self):
        actions = WindowsActions()
        request = actions.propose("capture_screen", "desktop")
        with patch("jarvis.windows_actions.capture_screen_png") as capture:
            with self.assertRaises(PermissionError):
                actions.execute(request.token, "capture_screen", "desktop")
            capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()
