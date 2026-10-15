import json
import os
import sqlite3
import tempfile
import unittest
from jarvis.learning_docs import collect, extract, PAGES

HTML = b"<html><nav>BAD NAV</nav><main><h1>Python docs</h1><p>" + b"Useful official documentation content. " * 5 + b"</p></main></html>"

class DocumentationTests(unittest.TestCase):
    def test_extract_main_only(self):
        result = extract(HTML)
        self.assertIn("Useful official", result)
        self.assertNotIn("BAD NAV", result)

    def test_no_main_is_empty(self):
        self.assertEqual(extract(b"<html><p>Navigation only</p></html>"), "")

    def test_reject_oversized(self):
        with self.assertRaises(ValueError):
            extract(b"x" * (512 * 1024 + 1))

    def test_collect_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "learning.db")
            self.assertEqual(collect(db_path, lambda url: HTML)["documents_collected"], len(PAGES))
            self.assertEqual(collect(db_path, lambda url: HTML)["documents_collected"], 0)
            with sqlite3.connect(db_path) as db:
                rows = db.execute("SELECT status,evidence FROM learning_events WHERE kind='official_doc'").fetchall()
            self.assertEqual(len(rows), len(PAGES))
            self.assertTrue(all(status == "collected" for status, _ in rows))
            self.assertTrue(all(json.loads(raw)["scope"] == "unreviewed_document_excerpt" for _, raw in rows))

if __name__ == "__main__":
    unittest.main()
