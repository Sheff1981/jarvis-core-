"""Project export and explicit deletion through the conversational interface."""
import json
import os
import tempfile
import unittest
from jarvis.dialogue import Dialogue
from jarvis.conversation_memory import ConversationMemory


class DialogueProjectLifecycleTests(unittest.TestCase):
    def test_export_by_exact_name(self):
        with tempfile.TemporaryDirectory() as directory:
            dialogue = Dialogue(db_path=os.path.join(directory, "memory.db"))
            dialogue.projects.add("JARVIS")
            payload = json.loads(dialogue.respond("экспорт проекта JARVIS"))
            self.assertEqual(payload["project"]["name"], "JARVIS")
            self.assertEqual(dialogue.respond("экспорт проекта unknown"),
                             "Не найден ровно один проект с таким названием.")
            dialogue.close()

    def test_cancel_and_unrelated_input_expire_pending_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            dialogue = Dialogue(db_path=os.path.join(directory, "memory.db"))
            dialogue.projects.add("JARVIS")
            dialogue.respond("удали проект JARVIS")
            self.assertIn("отменено", dialogue.respond("отмена"))
            self.assertIn("Нет ожидающего", dialogue.respond(
                "подтверждаю удаление проекта JARVIS"))
            dialogue.respond("удали проект JARVIS")
            self.assertIn("Удаление отменено", dialogue.respond("привет"))
            self.assertEqual(len(dialogue.projects.list()), 1)
            dialogue.close()

    def test_delete_requires_matching_explicit_confirmation_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            dialogue = Dialogue(db_path=path)
            dialogue.projects.add("JARVIS")
            memory = ConversationMemory(path)
            memory.append("user", "keep this")
            prompt = dialogue.respond("удали проект JARVIS")
            self.assertIn("подтверждаю удаление проекта JARVIS", prompt)
            self.assertIn("Удаление отменено", dialogue.respond(
                "подтверждаю удаление проекта another"))
            self.assertEqual(len(dialogue.projects.list()), 1)
            dialogue.respond("удали проект JARVIS")
            result = dialogue.respond("подтверждаю удаление проекта JARVIS")
            self.assertIn("удалён", result)
            self.assertEqual(dialogue.projects.list(), [])
            self.assertEqual(memory.recent()[0]["content"], "keep this")
            memory.close()
            dialogue.close()


if __name__ == "__main__":
    unittest.main()
