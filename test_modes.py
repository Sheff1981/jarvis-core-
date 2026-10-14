import tempfile
import unittest
from unittest.mock import Mock
from jarvis.assistant import Assistant


class ModeTests(unittest.TestCase):
    def test_chat_never_calls_computer_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            llm = Mock()
            llm.max_turns = 8
            llm.history = []
            llm.ask.return_value = "Я слушаю."
            assistant = Assistant(db_path=folder + "/test.db", llm=llm)
            assistant.action_dialogue.respond = Mock(side_effect=AssertionError("tool invoked"))
            self.assertIn("поговорим", assistant.respond("Джарвис, давай поговорим"))
            self.assertEqual("Я слушаю.", assistant.respond("открой блокнот"))
            assistant.action_dialogue.respond.assert_not_called()
            self.assertIn("создать", assistant.respond("давай что-нибудь создадим"))
            assistant.close()

    def test_chat_cancels_pending_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            assistant = Assistant(db_path=folder + "/test.db", llm=Mock(max_turns=8, history=[]))
            assistant.respond("открой блокнот")
            self.assertIsNotNone(assistant.action_dialogue.pending)
            assistant.respond("режим разговора")
            self.assertIsNone(assistant.action_dialogue.pending)
            assistant.close()


if __name__ == "__main__":
    unittest.main()
