import json
import tempfile
import unittest
from pathlib import Path
from jarvis.dictionary_catalog import DictionaryCatalog
from jarvis.dictionary_index import DictionaryIndex


class DictionaryIndexTests(unittest.TestCase):
    def test_authorized_import_and_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = DictionaryCatalog(root / "catalog.db")
            catalog.register(source_id="sample", title="Sample", category="historical",
                             provenance="Local sample", license_status="permission",
                             license_evidence="Test fixture permission")
            index = DictionaryIndex(root / "index.db")
            path = root / "entries.jsonl"
            path.write_text(json.dumps({"lemma": "Слово", "definition": "Значение"},
                                       ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(index.import_jsonl(catalog, "sample", path), 1)
            self.assertEqual(index.lookup("слово")[0]["definition"], "Значение")
            self.assertEqual(index.lookup("слово")[0]["modern_norm"], 0)
            self.assertEqual(index.import_jsonl(catalog, "sample", path), 1)
            self.assertEqual(len(index.lookup("слово")), 1)

    def test_unlicensed_source_cannot_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = DictionaryCatalog(root / "catalog.db")
            catalog.register(source_id="unknown", title="Unknown", category="explanatory",
                             provenance="Unknown")
            path = root / "entries.jsonl"
            path.write_text('{"lemma":"слово","definition":"значение"}\n', encoding="utf-8")
            with self.assertRaises(PermissionError):
                DictionaryIndex(root / "index.db").import_jsonl(catalog, "unknown", path)

    def test_bad_entry_rolls_back_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = DictionaryCatalog(root / "catalog.db")
            catalog.register(source_id="sample", title="Sample", category="historical",
                             provenance="Local sample", license_status="permission",
                             license_evidence="Test fixture permission")
            index = DictionaryIndex(root / "index.db")
            path = root / "entries.jsonl"
            path.write_text('{"lemma":"первое","definition":"значение"}\n{"lemma":"","definition":"нет"}\n',
                            encoding="utf-8")
            with self.assertRaises(ValueError):
                index.import_jsonl(catalog, "sample", path)
            self.assertEqual(index.lookup("первое"), [])


if __name__ == "__main__":
    unittest.main()
