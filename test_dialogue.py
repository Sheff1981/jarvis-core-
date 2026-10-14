import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue import Dialogue

class DialogueTests(unittest.TestCase):
    def test_project_conversation_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "jarvis.db")
            jarvis = Dialogue(path)
            self.assertIn("Запомнил", jarvis.respond("добавь проект Магазин"))
            jarvis.close()
            jarvis = Dialogue(path)
            self.assertIn("Магазин", jarvis.respond("какие проекты у нас"))
            self.assertEqual(jarvis.respond("стоп"), "Останавливаюсь.")
            jarvis.close()

    def test_unknown_does_not_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            jarvis = Dialogue(str(Path(directory) / "jarvis.db"))
            self.assertIn("не умею", jarvis.respond("удали все файлы"))
            jarvis.close()

if __name__ == "__main__":
    unittest.main()
