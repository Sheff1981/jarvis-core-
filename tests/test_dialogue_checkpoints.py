"""Dialogue recovery of the latest durable project checkpoint."""
import os
import tempfile
import unittest
from jarvis.dialogue import Dialogue


class DialogueCheckpointTests(unittest.TestCase):
    def test_recovery_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "jarvis.db")
            first = Dialogue(db_path=path)
            project_id = first.projects.add("JARVIS")
            first.projects.checkpoint(project_id, stage="Memory Core",
                                      task="Integration", status="running",
                                      last_action="saved checkpoint",
                                      evidence="local test", blockers="",
                                      next_step="verify CI")
            first.close()
            second = Dialogue(db_path=path)
            answer = second.respond("на чём остановились")
            self.assertIn("Memory Core", answer)
            self.assertIn("verify CI", answer)
            second.close()

    def test_empty_and_legacy_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            dialogue = Dialogue(db_path=os.path.join(tmp, "jarvis.db"))
            self.assertIn("Нет сохранённых", dialogue.respond("продолжим проект"))
            dialogue.projects.add("Legacy", "continue")
            self.assertIn("continue", dialogue.respond("продолжим проект"))
            dialogue.close()


if __name__ == "__main__":
    unittest.main()
