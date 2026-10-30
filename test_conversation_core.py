import unittest
import tempfile
from pathlib import Path
from jarvis.conversation_store import ConversationStore
from unittest.mock import patch
from jarvis.conversation_core import JarvisConversation


class ConversationCoreTests(unittest.TestCase):
    @patch("jarvis.conversation_core.LocalLLM")
    def test_private_sessions_and_context(self, backend):
        backend.return_value.ask.return_value = "Ответ"
        core = JarvisConversation(max_sessions=2)
        self.assertEqual(core.ask("Привет"), "Ответ")
        self.assertEqual(core.ask("Как дела?"), "Ответ")
        self.assertEqual(backend.call_count, 1)
        core.ask("Привет", session_id="other")
        self.assertEqual(backend.call_count, 2)
        with self.assertRaises(RuntimeError):
            core.ask("Привет", session_id="third")
        self.assertTrue(core.close_session("other"))
        self.assertFalse(core.close_session("other"))

    @patch("jarvis.conversation_core.LocalLLM")
    def test_dictionary_provenance_and_historical_marker(self, backend):
        class Dictionary:
            def lookup(self, word, limit):
                return [{"definition": "Старое значение", "source_id": "dahl",
                         "modern_norm": 0}] if word == "слово" else []
        core = JarvisConversation(dictionary=Dictionary())
        core.ask("Объясни слово")
        prompt = backend.return_value.ask.call_args.args[0]
        self.assertIn("Старое значение", prompt)
        self.assertIn('"historical": true', prompt)

    @patch("jarvis.conversation_core.LocalLLM")
    def test_existing_memory_is_opt_in(self, backend):
        backend.return_value.ask.return_value = "Ответ"
        with tempfile.TemporaryDirectory() as folder:
            store = ConversationStore(Path(folder) / "chat.db")
            try:
                core = JarvisConversation(memory_store=store, save_history=True)
                core.ask("Привет")
                self.assertEqual(len(store.recent()), 2)
                core.close_session()
                core.ask("Снова")
                self.assertEqual(len(store.recent()), 4)
            finally:
                store.close()

    @patch("jarvis.conversation_core.LocalLLM")
    def test_failed_answer_is_not_saved(self, backend):
        backend.return_value.ask.side_effect = RuntimeError("Offline")
        with tempfile.TemporaryDirectory() as folder:
            store = ConversationStore(Path(folder) / "chat.db")
            try:
                core = JarvisConversation(memory_store=store, save_history=True)
                with self.assertRaises(RuntimeError):
                    core.ask("Привет")
                self.assertEqual(store.recent(), [])
            finally:
                store.close()

    def test_rejects_bad_session_and_empty_input(self):
        core = JarvisConversation()
        with self.assertRaises(ValueError):
            core.ask(" ")
        with self.assertRaises(ValueError):
            core.ask("Привет", session_id="../other")


if __name__ == "__main__":
    unittest.main()
