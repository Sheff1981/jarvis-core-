import tempfile
import unittest
from pathlib import Path
from jarvis.assistant import Assistant


class OfflineOnly:
    def ask(self, prompt):
        raise AssertionError("Action approval must not reach LLM")


class ActionDialogueTests(unittest.TestCase):
    def test_approval_is_required_before_listing(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "sample.txt").write_text("test", encoding="utf-8")
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=OfflineOnly())
            try:
                prompt = assistant.respond("покажи содержимое папки " + folder)
                self.assertIn("Разрешаешь", prompt)
                self.assertIn("sample.txt", assistant.respond("разрешаю"))
                self.assertEqual(assistant.action_dialogue.pending, None)
            finally:
                assistant.close()

    def test_denial_does_not_read_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            assistant = Assistant(str(Path(folder) / "memory.db"), llm=OfflineOnly())
            try:
                assistant.respond("что в папке " + folder)
                self.assertIn("отменено", assistant.respond("нет"))
                self.assertEqual(assistant.action_dialogue.actions.audit, [])
            finally:
                assistant.close()


if __name__ == "__main__":
    unittest.main()
