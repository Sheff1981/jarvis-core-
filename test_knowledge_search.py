import os
import tempfile
import unittest
from jarvis.learning import LearningJournal
from jarvis.knowledge_search import search

class KnowledgeSearchTests(unittest.TestCase):
    def test_search_only_official_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "learning.db")
            journal = LearningJournal(path)
            journal.record("official_doc", "sqlite3.html", "collected", {
                "excerpt": "SQLite is an embedded database engine.",
                "url": "https://docs.python.org/3/library/sqlite3.html",
                "scope": "unreviewed_document_excerpt"})
            journal.record("rss", "SQLite rumor", "collected", {"url": "https://example.com"})
            result = search(path, "SQLite")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["status"], "collected")
            self.assertIn("docs.python.org", result[0]["source_url"])

    def test_no_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "learning.db")
            LearningJournal(path)
            self.assertEqual(search(path, "unfindable"), [])
            self.assertEqual(search(path, "a"), [])

if __name__ == "__main__":
    unittest.main()
