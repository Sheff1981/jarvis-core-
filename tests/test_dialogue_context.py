"""Integration checks for project-scoped dialogue context."""
import os
import tempfile
import unittest

from jarvis.dialogue_context import build_project_context
from jarvis.dialogue_memory import DialogueMemory
from jarvis.projects import Projects


class ProjectContextTests(unittest.TestCase):
    def test_context_and_isolation_after_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "jarvis.db")
            projects = Projects(path)
            first = projects.add("JARVIS", "Connect context to dialogue")
            second = projects.add("Unrelated", "Keep separate")
            projects.close()
            memory = DialogueMemory(path)
            memory.append(first, "user", "Where did we stop?")
            memory.append(second, "user", "Other project's private context")
            memory.append(first, "assistant", "At dialogue memory")
            memory.close()
            result = build_project_context(first, path)
            self.assertEqual(result["project_name"], "JARVIS")
            self.assertEqual(result["next_step"], "Connect context to dialogue")
            self.assertEqual([x["content"] for x in result["messages"]],
                             ["Where did we stop?", "At dialogue memory"])
            self.assertNotIn("Other project's private context", str(result))
            with self.assertRaises(KeyError):
                build_project_context("unknown", path)

    def test_completed_project_remains_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "jarvis.db")
            projects = Projects(path)
            pid = projects.add("Finished")
            projects.update(pid, status="done")
            projects.close()
            self.assertEqual(build_project_context(pid, path)["status"], "done")


if __name__ == "__main__":
    unittest.main()
