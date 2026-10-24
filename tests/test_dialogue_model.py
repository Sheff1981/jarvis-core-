import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue import Dialogue
from jarvis.local_model import LocalModelError


class FakeModel:
    def __init__(self):
        self.messages = None

    def reply(self, messages):
        self.messages = messages
        return "Давай поговорим."


class FailingModel:
    def reply(self, messages):
        raise LocalModelError("offline")


class DialogueModelTests(unittest.TestCase):
    def test_freeform_uses_local_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = FakeModel()
            dialogue = Dialogue(str(Path(tmp) / "db.sqlite"), model=model)
            try:
                self.assertEqual(dialogue.respond("Как дела?"), "Давай поговорим.")
                self.assertEqual(model.messages[-1]["content"], "Как дела?")
            finally:
                dialogue.close()

    def test_model_failure_does_not_break_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            dialogue = Dialogue(str(Path(tmp) / "db.sqlite"), model=FailingModel())
            try:
                self.assertIn("недоступна", dialogue.respond("Расскажи историю"))
                self.assertIn("Запомнил проект", dialogue.respond("добавь проект Сад"))
            finally:
                dialogue.close()

    def test_commands_do_not_invoke_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = FakeModel()
            dialogue = Dialogue(str(Path(tmp) / "db.sqlite"), model=model)
            try:
                dialogue.respond("режим беседы")
                self.assertIsNone(model.messages)
            finally:
                dialogue.close()
