"""Regression tests for authoritative project inventory routing."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from jarvis.assistant import Assistant


class ProjectInventoryRoutingTests(unittest.TestCase):
    def test_project_queries_use_sqlite_without_llm(self):
        with tempfile.TemporaryDirectory() as directory:
            llm = Mock()
            llm.ask.return_value = "Придуманный проект"
            with patch("jarvis.assistant.WindowsActions"):
                assistant = Assistant(db_path=str(Path(directory) / "jarvis.db"), llm=llm)
                try:
                    assistant.dialogue.projects.add("Лизория", "Проверить сайт")
                    for phrase in (
                        "Какие у нас проекты?",
                        "Джарвис, какие у нас проекты?",
                        "Покажи мои проекты",
                        "Перечисли наши проекты.",
                        "Список наших проектов",
                    ):
                        with self.subTest(phrase=phrase):
                            reply = assistant.respond(phrase)
                            self.assertIn("Лизория", reply)
                            self.assertIn("Проверить сайт", reply)
                    llm.ask.assert_not_called()
                finally:
                    assistant.close()

    def test_empty_inventory_does_not_hallucinate(self):
        with tempfile.TemporaryDirectory() as directory:
            llm = Mock()
            with patch("jarvis.assistant.WindowsActions"):
                assistant = Assistant(db_path=str(Path(directory) / "jarvis.db"), llm=llm)
                try:
                    self.assertIn("пока нет", assistant.respond("Какие у нас проекты?"))
                    llm.ask.assert_not_called()
                finally:
                    assistant.close()


if __name__ == "__main__":
    unittest.main()
