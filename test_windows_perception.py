import unittest
from unittest.mock import patch

from jarvis.action_dialogue import ActionDialogue
from jarvis.windows_actions import WindowsActions


class WindowListingTests(unittest.TestCase):
    def test_listing_needs_explicit_permission(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.list_visible_windows", return_value=["Notes", "Browser"]) as windows:
            self.assertIn("Разрешаешь", dialogue.respond("какие окна открыты"))
            windows.assert_not_called()
            self.assertIn("Notes", dialogue.respond("разрешаю"))
            windows.assert_called_once()

    def test_refusal_blocks_window_inspection(self):
        dialogue = ActionDialogue()
        with patch("jarvis.windows_actions.list_visible_windows") as windows:
            dialogue.respond("покажи открытые окна")
            dialogue.respond("нет")
            windows.assert_not_called()

    def test_unapproved_window_list_is_rejected(self):
        actions = WindowsActions()
        request = actions.propose("list_windows", "desktop")
        with self.assertRaises(PermissionError):
            actions.execute(request.token, "list_windows", "desktop")


if __name__ == "__main__":
    unittest.main()
