import tempfile
import unittest
from pathlib import Path

from jarvis.learning import LearningJournal
from jarvis.learning_collector import collect, parse_feed


FEED = b"""<rss><channel>
<item><title>Release notes</title><link>https://www.python.org/news/1</link></item>
<item><title>Unsafe</title><link>http://example.com/2</link></item>
</channel></rss>"""


class LearningCollectorTests(unittest.TestCase):
    def test_collect_once_and_mark_unverified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "learning.db")
            fetch = lambda url: FEED
            self.assertEqual(collect("https://www.python.org/blogs/rss/", path, fetch), 1)
            self.assertEqual(collect("https://www.python.org/blogs/rss/", path, fetch), 0)
            report = LearningJournal(path).daily_report()
            self.assertEqual(report["total"], 1)
            self.assertEqual(report["verified"], 0)
            self.assertEqual(report["events"][0]["status"], "collected")

    def test_rejects_non_https_feed(self):
        with self.assertRaises(ValueError):
            collect("http://example.com/rss", ":memory:", lambda url: FEED)

    def test_rejects_oversized_feed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                collect("https://www.python.org/rss", str(Path(folder) / "db"),
                        lambda url: b"x" * (1024 * 1024 + 1))
