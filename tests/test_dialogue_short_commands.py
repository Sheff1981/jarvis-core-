"""Regression coverage for short natural-language project commands."""
import tempfile
import unittest
from pathlib import Path

from jarvis.dialogue import Dialogue
from jarvis.session import Mode


class ShortCommandTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.dialogue = Dialogue(db_path=str(Path(self.folder.name) / "jarvis.db"))

    def tearDown(self):
        self.dialogue.close()
        self.folder.cleanup()

    def test_project_name_can_be_provided_in_followup(self):
        self.assertEqual(self.dialogue.respond("Добавь проект"), "Назови проект.")
        self.assertEqual(self.dialogue.projects.list(), [])
        self.assertIn("Проверка", self.dialogue.respond("Проверка"))
        self.assertIn("Следующий шаг", self.dialogue.respond("Настроить голос"))
        projects = self.dialogue.projects.list()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "Проверка")
        self.assertEqual(projects[0]["next_step"], "Настроить голос")

    def test_cancel_discards_pending_project_name(self):
        self.dialogue.respond("Добавь проект")
        self.dialogue.respond("отмена")
        self.dialogue.respond("Случайный текст")
        self.assertEqual(self.dialogue.projects.list(), [])

    def test_stop_discards_pending_project_name(self):
        self.dialogue.respond("Добавь проект")
        self.dialogue.respond("стоп")
        self.dialogue.respond("Случайный текст")
        self.assertEqual(self.dialogue.projects.list(), [])

    def test_project_list_discards_pending_project_name(self):
        self.dialogue.respond("Добавь проект")
        self.dialogue.respond("какие проекты")
        self.dialogue.respond("Случайный текст")
        self.assertEqual(self.dialogue.projects.list(), [])

    def test_mode_switch_discards_pending_project_name(self):
        self.dialogue.respond("Добавь проект")
        self.dialogue.respond("Работай")
        self.dialogue.respond("Случайный текст")
        self.assertEqual(self.dialogue.projects.list(), [])

    def test_workay_switches_session_mode_without_actions(self):
        response = self.dialogue.respond("Работай")
        self.assertIn("Рабочий режим", response)
        self.assertEqual(self.dialogue.session.mode, Mode.WORK)


if __name__ == "__main__":
    unittest.main()
