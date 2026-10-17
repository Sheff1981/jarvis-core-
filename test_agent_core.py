import tempfile
import unittest
from pathlib import Path
from jarvis.agent_core import AgentCore, PlannedAction


class AgentCoreTests(unittest.TestCase):
    def test_multistep_plan_requires_separate_approvals(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.txt"
            path.write_text("abc", encoding="utf-8")
            agent = AgentCore()
            agent.set_plan([
                PlannedAction("list_directory", folder, "inspect folder"),
                PlannedAction("file_info", str(path), "inspect file"),
            ])
            first = agent.next_request()
            self.assertEqual(agent.next_request().token, first.token)
            self.assertEqual(agent.resolve(first.token, True)["status"], "completed")
            second = agent.next_request()
            self.assertNotEqual(first.token, second.token)
            with self.assertRaises(PermissionError):
                agent.resolve(first.token, True)
            self.assertEqual(agent.resolve(second.token, True)["result"]["size"], 3)
            self.assertIsNone(agent.next_request())

    def test_denial_cancels_remaining_steps(self):
        agent = AgentCore()
        agent.set_plan([PlannedAction("list_directory", ".", "inspect")])
        request = agent.next_request()
        self.assertEqual(agent.resolve(request.token, False)["status"], "denied")
        self.assertIsNone(agent.next_request())

    def test_no_unsafe_steps_or_approval_bypass(self):
        agent = AgentCore()
        with self.assertRaises(ValueError):
            agent.set_plan([PlannedAction("delete", "C:/", "cleanup")])
        agent.set_plan([PlannedAction("list_directory", ".", "inspect")])
        request = agent.next_request()
        with self.assertRaises(PermissionError):
            agent.resolve("fabricated-token", True)
        self.assertEqual(agent.resolve(request.token, False)["status"], "denied")


if __name__ == "__main__":
    unittest.main()
