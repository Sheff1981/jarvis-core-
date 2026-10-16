"""Russian dialogue commands for deferred ideas and decisions."""
import os
import tempfile
import unittest
from jarvis.dialogue import Dialogue


class DialogueIdeaTests(unittest.TestCase):
    def test_idea_is_queued_without_changing_current_step(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            dialogue = Dialogue(db_path=path)
            dialogue.respond("запомни проект JARVIS")
            dialogue.respond("Завершить Memory Core")
            response = dialogue.respond("отложи идею создать аватар")
            self.assertIn("не меняю", response)
            self.assertIn("создать аватар", dialogue.respond("список идей"))
            self.assertIn("Завершить Memory Core", dialogue.respond("на чём остановились"))
            dialogue.respond("запиши решение не менять main")
            self.assertEqual(dialogue.projects.decisions(
                dialogue.projects.list()[0]["id"])[0]["decision"], "не менять main")
            dialogue.close()
            reopened = Dialogue(db_path=path)
            self.assertIn("создать аватар", reopened.respond("список идей"))
            self.assertIn("Завершить Memory Core", reopened.respond("на чём остановились"))
            reopened.close()

    def test_no_project_does_not_create_orphan_idea(self):
        with tempfile.TemporaryDirectory() as directory:
            dialogue = Dialogue(db_path=os.path.join(directory, "memory.db"))
            self.assertIn("Сначала создай проект",
                          dialogue.respond("идея на потом новая тема"))
            dialogue.close()


if __name__ == "__main__":
    unittest.main()
