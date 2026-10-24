"""Read-only research agent policy tests without external network access."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.academy import Academy
from jarvis.research_agent import ResearchAgent, ResearchResult


class ResearchAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.academy = Academy(str(Path(self.temp.name) / "academy.db"))

    def tearDown(self):
        self.academy.close()
        self.temp.cleanup()

    def test_official_documentation_only(self):
        agent = ResearchAgent(self.academy)
        with self.assertRaises(ValueError):
            agent.study("https://attacker.invalid/", "python")

    def test_no_unverified_knowledge_is_promoted(self):
        agent = ResearchAgent(self.academy)
        with patch.object(agent, "validate_public_url"), patch.object(
            self.academy, "ingest",
            return_value={"url": "https://docs.python.org/3/", "characters": 123}
        ):
            result = agent.study("https://docs.python.org/3/", "python")
        self.assertIsInstance(result, ResearchResult)
        self.assertEqual(result.status, "pending_review")
        self.assertEqual(result.route, "direct")

    def test_batch_is_bounded_and_failures_are_recorded(self):
        agent = ResearchAgent(self.academy)
        entries = [("https://attacker.invalid/", "python")] * 25
        outcomes = agent.study_batch(entries, max_pages=3)
        self.assertEqual(len(outcomes), 3)
        self.assertTrue(all("error" in item for item in outcomes))
        with self.assertRaises(ValueError):
            agent.study_batch(entries, max_pages=100)

    def test_private_addresses_rejected(self):
        with self.assertRaises(ValueError):
            ResearchAgent.validate_public_url("https://127.0.0.1/")
        with self.assertRaises(ValueError):
            ResearchAgent.validate_public_url("http://docs.python.org/")


if __name__ == "__main__":
    unittest.main()
