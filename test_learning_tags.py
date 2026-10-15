"""Tests for bounded, idempotent CPython tag metadata collection."""
import json
import os
import sqlite3
import tempfile
import unittest

from jarvis.learning import LearningJournal
from jarvis.learning_tags import BASE, collect, tag_metadata


class LearningTagsTests(unittest.TestCase):
    def test_annotated_tag(self):
        sha = "a" * 40
        commit = "b" * 40
        def fetch(url):
            if url == BASE + "git/ref/tags/v3.14.8":
                return {"ref": "refs/tags/v3.14.8", "object": {"type": "tag", "sha": sha}}
            if url == BASE + "git/tags/" + sha:
                return {"tag": "v3.14.8", "object": {"type": "commit", "sha": commit}}
            raise AssertionError(url)
        result = tag_metadata("v3.14.8", fetch)
        self.assertEqual(result["commit_sha"], commit)
        self.assertEqual(result["tag_sha"], sha)
        self.assertEqual(result["scope"], "tag_metadata_only")

    def test_rejects_invalid_tag(self):
        with self.assertRaises(ValueError):
            tag_metadata("../other", lambda url: {})

    def test_collection_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "learning.db")
            journal = LearningJournal(path)
            journal.record("rss", "v3.14.8", "collected",
                           {"url": "https://github.com/python/cpython/releases/tag/v3.14.8"})
            def fetch(url):
                return {"ref": "refs/tags/v3.14.8",
                        "object": {"type": "commit", "sha": "c" * 40}}
            self.assertEqual(collect(path, fetch)["tags_collected"], 1)
            self.assertEqual(collect(path, fetch)["tags_collected"], 0)
            with sqlite3.connect(path) as db:
                rows = db.execute("SELECT status,evidence FROM learning_events WHERE kind='release_tag'").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "collected")
            self.assertEqual(json.loads(rows[0][1])["commit_sha"], "c" * 40)


if __name__ == "__main__":
    unittest.main()
