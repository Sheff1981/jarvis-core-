import tempfile
import unittest
from pathlib import Path
from jarvis.dictionary_catalog import DictionaryCatalog


class DictionaryCatalogTests(unittest.TestCase):
    def test_unverified_license_blocks_import(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = DictionaryCatalog(Path(directory) / "sources.db")
            allowed = catalog.register(source_id="dahl", title="Словарь Даля",
                                       category="historical",
                                       provenance="Bibliographic reference")
            self.assertFalse(allowed)
            self.assertEqual(catalog.list_sources(importable_only=True), [])
            self.assertEqual(catalog.list_sources()[0]["modern_norm"], 0)

    def test_verified_license_requires_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = DictionaryCatalog(Path(directory) / "sources.db")
            self.assertFalse(catalog.register(
                source_id="one", title="Словарь 1", category="orthographic",
                provenance="Publisher", license_status="open_license",
                modern_norm=True))
            self.assertTrue(catalog.register(
                source_id="two", title="Словарь 2", category="orthographic",
                provenance="Publisher", license_status="open_license",
                license_evidence="License file reviewed", modern_norm=True))
            self.assertEqual(len(catalog.list_sources(importable_only=True)), 1)

    def test_invalid_category_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = DictionaryCatalog(Path(directory) / "sources.db")
            with self.assertRaises(ValueError):
                catalog.register(source_id="bad", title="Bad",
                                 category="all_the_internet", provenance="unknown")


if __name__ == "__main__":
    unittest.main()
