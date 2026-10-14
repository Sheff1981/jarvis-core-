import sys
import unittest
from unittest.mock import patch, MagicMock

import chat


class ChatEntrypointTests(unittest.TestCase):
    def test_unified_assistant_is_opt_in(self):
        with patch.object(sys, "argv", ["chat.py", "--assistant", "--model", "qwen2.5:3b"]), \
             patch("chat.Assistant") as assistant, \
             patch("chat.Dialogue") as dialogue, \
             patch("builtins.input", side_effect=EOFError):
            assistant.return_value = MagicMock()
            chat.main()
            assistant.assert_called_once_with(db_path="jarvis.db", model="qwen2.5:3b")
            dialogue.assert_not_called()
            assistant.return_value.close.assert_called_once()

    def test_default_keeps_legacy_dialogue(self):
        with patch.object(sys, "argv", ["chat.py"]), \
             patch("chat.Assistant") as assistant, \
             patch("chat.Dialogue") as dialogue, \
             patch("builtins.input", side_effect=EOFError):
            chat.main()
            dialogue.assert_called_once()
            assistant.assert_not_called()
            dialogue.return_value.close.assert_called_once()
