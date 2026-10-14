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
            self.assertIn("записан", jarvis.respond("Проверить карточки товаров"))
            jarvis.close()
            jarvis = Dialogue(path)
            answer = jarvis.respond("какие проекты у нас")
            self.assertIn("Магазин", answer)
            self.assertIn("Проверить карточки товаров", answer)
            self.assertEqual(jarvis.respond("стоп"), "Останавливаюсь.")
            jarvis.close()

    def test_cancel_pending_followup(self):
        with tempfile.TemporaryDirectory() as directory:
            jarvis = Dialogue(str(Path(directory) / "jarvis.db"))
            jarvis.respond("добавь проект Пример")
            self.assertIn("отменено", jarvis.respond("отмена"))
            self.assertIn("не умею", jarvis.respond("удали все файлы"))
            self.assertIn("не определён", jarvis.respond("какие проекты"))
            jarvis.close()

    def test_unknown_does_not_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            jarvis = Dialogue(str(Path(directory) / "jarvis.db"))
            self.assertIn("не умею", jarvis.respond("удали все файлы"))
            jarvis.close()


if __name__ == "__main__":
    unittest.main()
