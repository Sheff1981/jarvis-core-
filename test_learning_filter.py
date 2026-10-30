import tempfile
import unittest
from pathlib import Path
from jarvis.learning import LearningJournal
from jarvis.learning_filter import classify
from jarvis.learning_collector import collect

FEED = b"""<rss><channel>
<item><title>Python 3.14 release</title><link>https://example.org/python</link></item>
<item><title>Discount shoes</title><link>https://example.org/shoes</link></item>
</channel></rss>"""

class TopicFilterTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(classify("CVE-2026-1234 security patch"), "security")
        self.assertEqual(classify("New LLM transformer"), "ai")
        self.assertEqual(classify("Python 3.14 release"), "python")
        self.assertEqual(classify("Discount shoes"), "irrelevant")

    def test_filter_and_keep_unverified(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "learning.db")
            self.assertEqual(collect("https://example.org/rss", db, lambda _: FEED), 1)
            events = LearningJournal(db).daily_report()["events"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["status"], "collected")
            self.assertEqual(events[0]["evidence"]["category"], "python")
