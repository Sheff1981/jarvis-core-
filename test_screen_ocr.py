import unittest
from unittest.mock import patch
from jarvis.action_dialogue import ActionDialogue


class ScreenOCRTests(unittest.TestCase):
    def test_ocr_runs_only_after_explicit_consent(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.capture_screen_png", return_value=b"image") as capture:
            with patch("jarvis.windows_actions.recognize_screen_text", return_value="Hello") as ocr:
                self.assertIn("Разрешаешь", dialogue.respond("прочитай экран"))
                capture.assert_not_called()
                ocr.assert_not_called()
                self.assertIn("Hello", dialogue.respond("разрешаю"))
                capture.assert_called_once()
                ocr.assert_called_once_with(b"image")

    def test_refusal_blocks_capture_and_ocr(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.capture_screen_png") as capture:
            dialogue.respond("что написано на экране")
            dialogue.respond("нет")
            capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()
