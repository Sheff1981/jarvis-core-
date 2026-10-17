import tempfile
import unittest
from pathlib import Path
from jarvis.conversation_memory import ConversationMemory
from jarvis.dialogue import Dialogue


class EchoModel:
    def __init__(self):
        self.messages = []
    def reply(self, messages):
        self.messages = messages
        return "Ответ"


class ConversationPersistenceTests(unittest.TestCase):
    def test_roundtrip_and_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "memory.db")
            store = ConversationMemory(path)
            store.append("user", "Привет")
            store.close()
            store = ConversationMemory(path)
            self.assertEqual(store.recent(), [{"role": "user", "content": "Привет"}])
            store.clear()
            self.assertEqual(store.recent(), [])
            store.close()

    def test_dialogue_recalls_previous_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "memory.db")
            first = Dialogue(path, model=EchoModel())
            first.respond("Я люблю лес")
            first.close()
            model = EchoModel()
            second = Dialogue(path, model=model)
            try:
                second.respond("Что я говорил?")
                self.assertIn({"role": "user", "content": "Я люблю лес"}, model.messages)
                self.assertEqual(model.messages[-1]["content"], "Что я говорил?")
            finally:
                second.close()
