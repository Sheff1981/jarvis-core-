import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue import Dialogue
from jarvis.session import Mode


class DialogueModeTests(unittest.TestCase):
    def test_mode_transitions_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dialogue = Dialogue(str(Path(tmp) / "jarvis.db"))
            try:
                self.assertEqual(dialogue.session.mode, Mode.CONVERSATION)
                self.assertIn("Рабочий режим", dialogue.respond("рабочий режим"))
                self.assertEqual(dialogue.session.mode, Mode.WORK)
                self.assertIn("разговорный режим", dialogue.respond("режим беседы"))
                self.assertEqual(dialogue.session.mode, Mode.CONVERSATION)
            finally:
                dialogue.close()

    def test_unknown_command_does_not_switch_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            dialogue = Dialogue(str(Path(tmp) / "jarvis.db"))
            try:
                dialogue.respond("скачай торрент")
                self.assertEqual(dialogue.session.mode, Mode.CONVERSATION)
            finally:
                dialogue.close()
