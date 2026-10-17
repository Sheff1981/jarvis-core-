import tempfile
import unittest
from pathlib import Path
from jarvis.conversation_store import ConversationStore
from jarvis.assistant import Assistant


class MemoryLLM:
    max_turns = 8

    def __init__(self):
        self.history = []

    def ask(self, prompt):
        self.history.extend([{"role": "user", "content": prompt},
                             {"role": "assistant", "content": "ответ: " + prompt}])
        return "ответ: " + prompt

    def clear_history(self):
        self.history.clear()


class ConversationPersistenceTests(unittest.TestCase):
    def test_store_survives_restart_and_keeps_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            store = ConversationStore(path)
            store.append_exchange("первый", "ответ один")
            store.append_exchange("второй", "ответ два")
            store.close()
            reopened = ConversationStore(path)
            self.assertEqual(reopened.recent(1), [
                {"role": "user", "content": "второй"},
                {"role": "assistant", "content": "ответ два"},
            ])
            reopened.clear()
            self.assertEqual(reopened.recent(), [])
            reopened.close()

    def test_chat_history_survives_mode_switch_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            first = Assistant(path, llm=MemoryLLM())
            first.respond("давай поговорим")
            self.assertEqual("ответ: как прошёл день", first.respond("как прошёл день"))
            first.respond("давай поработаем")
            first.close()

            llm = MemoryLLM()
            second = Assistant(path, llm=llm)
            self.assertEqual(llm.history, [
                {"role": "user", "content": "как прошёл день"},
                {"role": "assistant", "content": "ответ: как прошёл день"},
            ])
            second.close()

    def test_assistant_restores_llm_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            first = Assistant(path, llm=MemoryLLM())
            first.respond("Объясни квантовую физику")
            first.close()
            llm = MemoryLLM()
            second = Assistant(path, llm=llm)
            self.assertEqual(llm.history, [
                {"role": "user", "content": "Объясни квантовую физику"},
                {"role": "assistant", "content": "ответ: Объясни квантовую физику"},
            ])
            second.clear_conversation()
            self.assertEqual(llm.history, [])
            second.close()


if __name__ == "__main__":
    unittest.main()
