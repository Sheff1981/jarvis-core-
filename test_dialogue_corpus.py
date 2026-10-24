import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue_corpus import DialogueCorpus


class DialogueCorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "dialogues.db"
        self.corpus = DialogueCorpus(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_consent_and_review_required_for_export(self):
        with self.assertRaises(PermissionError):
            self.corpus.submit("Привет", "Здравствуйте", source="owner")
        self.assertTrue(self.corpus.submit("Привет", "Здравствуйте", source="owner", consent=True))
        self.assertEqual(self.corpus.export_approved(), [])
        digest = self.corpus.pending()[0]["digest"]
        with self.assertRaises(PermissionError):
            self.corpus.review(digest)
        self.assertTrue(self.corpus.review(digest, approved=True))
        self.assertFalse(self.corpus.review(digest, approved=True))
        self.assertEqual(self.corpus.export_approved()[0]["messages"][1]["content"], "Здравствуйте")

    def test_duplicate_and_untrusted_source(self):
        self.assertTrue(self.corpus.submit("Как дела?", "Хорошо", source="curated", consent=True))
        self.assertFalse(self.corpus.submit("Как дела?", "Хорошо", source="curated", consent=True))
        with self.assertRaises(ValueError):
            self.corpus.submit("Текст", "Ответ", source="web", consent=True)

    def test_restart_persists_approval(self):
        self.corpus.submit("Вопрос", "Ответ", source="owner", consent=True)
        digest = self.corpus.pending()[0]["digest"]
        self.corpus.review(digest, approved=True)
        self.assertEqual(len(DialogueCorpus(self.path).export_approved()), 1)

    def test_approval_cannot_be_forged_with_sql_null(self):
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO dialogue_corpus(digest,user_text,assistant_text,source,consent,created_at) VALUES('x','a','b','owner',0,'now')")


if __name__ == "__main__":
    unittest.main()
