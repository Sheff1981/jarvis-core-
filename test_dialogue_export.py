import json
import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue_corpus import DialogueCorpus
from jarvis.dialogue_export import export_jsonl


class DialogueExportTests(unittest.TestCase):
    def test_only_approved_examples_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "corpus.db"
            output = Path(directory) / "train.jsonl"
            corpus = DialogueCorpus(db)
            corpus.submit("Вопрос один", "Ответ один", source="owner", consent=True)
            corpus.submit("Вопрос два", "Ответ два", source="owner", consent=True)
            with self.assertRaises(ValueError):
                export_jsonl(db, output, min_examples=1)
            self.assertFalse(output.exists())
            corpus.review(corpus.pending()[0]["digest"], approved=True)
            result = export_jsonl(db, output, min_examples=1)
            self.assertEqual(result["examples"], 1)
            self.assertFalse(result["trained"])
            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["messages"][0]["content"], "Вопрос один")
            with self.assertRaises(FileExistsError):
                export_jsonl(db, output, min_examples=1)


if __name__ == "__main__":
    unittest.main()
