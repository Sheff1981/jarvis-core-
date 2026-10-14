import tempfile
import unittest
from pathlib import Path

from jarvis.dialogue import Dialogue


class DialoguePrivacyTests(unittest.TestCase):
    def test_clear_conversation_does_not_delete_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            dialogue = Dialogue(db_path=path)
            try:
                dialogue.conversation.append("user", "Секретный текст")
                dialogue.conversation.append("assistant", "Ответ")
                dialogue.respond("добавь проект JARVIS")
                dialogue.respond("Сделать голос")
                result = dialogue.respond("очисти историю разговора")
                self.assertIn("удалена", result)
                self.assertEqual(dialogue.conversation.recent(), [])
                self.assertEqual(dialogue.session.history, [])
                self.assertIn("JARVIS", dialogue.respond("какие проекты"))
            finally:
                dialogue.close()

    def test_stop_resets_session_and_pending_project(self):
        with tempfile.TemporaryDirectory() as folder:
            dialogue = Dialogue(db_path=str(Path(folder) / "memory.db"))
            try:
                dialogue.respond("добавь проект TEST")
                self.assertIsNotNone(dialogue.pending_project_id)
                self.assertEqual(dialogue.respond("стоп"), "Останавливаюсь.")
                self.assertIsNone(dialogue.pending_project_id)
                self.assertEqual(dialogue.session.history, [])
            finally:
                dialogue.close()

    def test_rejects_non_text(self):
        with tempfile.TemporaryDirectory() as folder:
            dialogue = Dialogue(db_path=str(Path(folder) / "memory.db"))
            try:
                with self.assertRaises(TypeError):
                    dialogue.respond(None)
            finally:
                dialogue.close()
