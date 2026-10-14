import tempfile
import unittest
from pathlib import Path
from jarvis.assistant import Assistant


class StubLLM:
    def __init__(self):
        self.prompts = []

    def ask(self, prompt):
        self.prompts.append(prompt)
        return "Ответ модели"


class AssistantTests(unittest.TestCase):
    def test_projects_never_leave_local_router(self):
        with tempfile.TemporaryDirectory() as folder:
            llm = StubLLM()
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=llm)
            self.assertIn("Запомнил", assistant.respond("добавь проект LIZORIA"))
            assistant.respond("Проверить сборку")
            self.assertIn("Проверить сборку", assistant.respond("какие проекты"))
            self.assertEqual(llm.prompts, [])
            assistant.close()

    def test_general_question_uses_llm(self):
        with tempfile.TemporaryDirectory() as folder:
            llm = StubLLM()
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=llm)
            self.assertEqual(assistant.respond("Объясни, что такое Python"), "Ответ модели")
            self.assertEqual(llm.prompts, ["Объясни, что такое Python"])
            assistant.close()


if __name__ == "__main__":
    unittest.main()
