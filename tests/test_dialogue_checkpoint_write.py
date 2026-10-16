"""Dialogue can create a durable checkpoint through an explicit command."""
import os
import tempfile
import unittest
from jarvis.dialogue import Dialogue


class DialogueCheckpointWriteTests(unittest.TestCase):
    def test_checkpoint_command_persists_and_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.db")
            first = Dialogue(db_path=path)
            first.projects.add("JARVIS")
            response = first.respond(
                "контрольная точка: Memory Core; dialogue integration; running; verify CI; CI pending")
            self.assertIn("сохранена", response)
            first.close()
            second = Dialogue(db_path=path)
            answer = second.respond("на чём остановились")
            self.assertIn("dialogue integration", answer)
            self.assertIn("verify CI", answer)
            self.assertIn("CI pending", answer)
            second.close()

    def test_invalid_checkpoint_is_not_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            dialogue = Dialogue(db_path=os.path.join(directory, "memory.db"))
            dialogue.projects.add("JARVIS")
            self.assertIn("Формат:", dialogue.respond("контрольная точка: broken"))
            self.assertIsNone(dialogue.projects.latest_checkpoint(
                dialogue.projects.list()[0]["id"]))
            self.assertIn("Неизвестный статус", dialogue.respond(
                "контрольная точка: Stage; Task; unknown; Next"))
            self.assertIsNone(dialogue.projects.latest_checkpoint(
                dialogue.projects.list()[0]["id"]))
            dialogue.close()


if __name__ == "__main__":
    unittest.main()
