import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from jarvis.assistant import Assistant


class AssistantSafetyTests(unittest.TestCase):
    def test_empty_input_never_invokes_model_or_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            llm = Mock()
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=llm)
            try:
                assistant.action_dialogue.respond = Mock(side_effect=AssertionError("tool called"))
                self.assertEqual(assistant.respond("  "), "Я слушаю.")
                llm.ask.assert_not_called()
                assistant.action_dialogue.respond.assert_not_called()
            finally:
                assistant.close()

    def test_stop_cancels_pending_action_without_running_it(self):
        with tempfile.TemporaryDirectory() as folder:
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=Mock())
            try:
                assistant.respond("открой блокнот")
                self.assertIsNotNone(assistant.action_dialogue.pending)
                self.assertIn("отменено", assistant.respond("стоп"))
                self.assertIsNone(assistant.action_dialogue.pending)
            finally:
                assistant.close()

    def test_non_text_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=Mock())
            try:
                with self.assertRaises(TypeError):
                    assistant.respond(None)
            finally:
                assistant.close()
