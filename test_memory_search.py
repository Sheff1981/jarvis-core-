import tempfile
import unittest
from pathlib import Path
from jarvis.assistant import Assistant
from jarvis.conversation_store import ConversationStore


class NoNetworkLLM:
    def ask(self, prompt):
        raise AssertionError("Memory search must not invoke the LLM")


class SearchTests(unittest.TestCase):
    def test_cyrillic_search_newest_first(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ConversationStore(str(Path(folder) / "test.db"))
            store.append_exchange("Проект LIZORIA", "Делаем локальную память")
            store.append_exchange("Проект QUINTUM", "Обсудили тесты")
            store.append_exchange("Тест памяти", "Только локально")
            self.assertEqual(
                store.search("lizoria"),
                [{"role": "user", "content": "Проект LIZORIA"}],
            )
            self.assertEqual(
                store.search("ПРОЕКТ", limit=1),
                [{"role": "user", "content": "Проект QUINTUM"}],
            )
            self.assertEqual(store.search("пАмЯтИ"), [{"role": "user", "content": "Тест памяти"}])
            self.assertEqual(store.search(""), [])
            store.close()

    def test_assistant_search_does_not_call_llm(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "test.db")
            store = ConversationStore(path)
            store.append_exchange("Обсудили LIZORIA", "Делаем сайт")
            store.close()
            assistant = Assistant(path, llm=NoNetworkLLM())
            answer = assistant.respond("найди в разговорах LIZORIA")
            self.assertIn("Обсудили LIZORIA", answer)
            self.assertIn("ничего не найдено", assistant.respond("найди в разговорах неизвестное"))
            assistant.close()


if __name__ == "__main__":
    unittest.main()
