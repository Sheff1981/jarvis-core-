import tempfile
import unittest
from pathlib import Path

from jarvis.assistant import Assistant


class StubModel:
    def __init__(self):
        self.history = []
        self.max_turns = 8
        self.mode = "work"
    def ask(self, prompt):
        self.history.extend([{"role": "user", "content": prompt},
                             {"role": "assistant", "content": "Понял"}])
        return "Понял"
    def clear_history(self):
        self.history.clear()


class ConversationResetTests(unittest.TestCase):
    def test_clear_removes_persistent_and_in_memory_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "jarvis.db")
            assistant = Assistant(db_path=path, llm=StubModel())
            try:
                assistant.respond("Расскажи о музыке")
                self.assertTrue(assistant.conversations.search("музыке"))
                assistant.clear_conversation()
                self.assertEqual(assistant.conversations.search("музыке"), [])
                self.assertEqual(assistant.dialogue.conversation.recent(), [])
                self.assertEqual(assistant.llm.history, [])
                self.assertEqual(assistant.dialogue.session.history, [])
            finally:
                assistant.close()

    def test_spoken_clear_in_chat_mode_clears_memory_without_llm(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "jarvis.db")
            model = StubModel()
            assistant = Assistant(db_path=path, llm=model)
            try:
                assistant.respond("Расскажи о музыке")
                self.assertTrue(assistant.conversations.search("музыке"))
                assistant.respond("режим разговора")
                answer = assistant.respond("забудь наш разговор")
                self.assertIn("удалена", answer)
                self.assertEqual(assistant.conversations.search("музыке"), [])
                self.assertEqual(model.history, [])
                self.assertEqual(assistant.dialogue.session.history, [])
            finally:
                assistant.close()
