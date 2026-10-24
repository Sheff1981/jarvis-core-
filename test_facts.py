import tempfile
import unittest
from pathlib import Path
from jarvis.assistant import Assistant


class OfflineOnly:
    def ask(self, prompt):
        raise AssertionError("Fact commands must never invoke the LLM")


class FactTests(unittest.TestCase):
    def test_fact_survives_restart_and_can_be_deleted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            first = Assistant(path, llm=OfflineOnly())
            result = first.respond("Для проекта LIZORIA запомни, что магазин на нашей CMS")
            self.assertIn("Запомнил", result)
            first.close()

            second = Assistant(path, llm=OfflineOnly())
            self.assertIn("магазин на нашей CMS",
                          second.respond("что ты помнишь о проекте LIZORIA"))
            self.assertEqual(second.respond("забудь факт 1"), "Факт удалён.")
            self.assertIn("фактов пока нет",
                          second.respond("что ты помнишь о проекте LIZORIA"))
            second.close()

    def test_duplicate_fact_reuses_id_across_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "memory.db")
            first = Assistant(path, llm=OfflineOnly())
            first.respond("Для проекта LIZORIA запомни, что сайт готов")
            first.close()
            second = Assistant(path, llm=OfflineOnly())
            result = second.respond("для проекта lizoria запомни, что САЙТ ГОТОВ")
            self.assertIn("факт 1", result)
            self.assertEqual(len(second.facts.list("LIZORIA")), 1)
            second.close()

    def test_fact_commands_do_not_touch_other_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=OfflineOnly())
            assistant.respond("Для проекта QUINTUM запомни, что нужен тест")
            self.assertIn("фактов пока нет",
                          assistant.respond("что ты помнишь о проекте LIZORIA"))
            assistant.close()


if __name__ == "__main__":
    unittest.main()
