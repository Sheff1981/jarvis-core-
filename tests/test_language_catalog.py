"""Programming language catalog coverage and progress tests."""
import tempfile
import unittest
from pathlib import Path
from jarvis.language_catalog import LanguageCatalog, SEED_LANGUAGES


class LanguageCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.catalog = LanguageCatalog(str(Path(self.temp.name) / "catalog.db"))

    def tearDown(self):
        self.catalog.close()
        self.temp.cleanup()

    def test_seed_does_not_claim_proficiency(self):
        self.catalog.seed()
        self.catalog.seed()
        rows = self.catalog.list()
        self.assertEqual(len(rows), len(SEED_LANGUAGES))
        self.assertTrue(all(row["status"] == "discovered" for row in rows))
        self.assertTrue(all(row["verified_exercises"] == 0 for row in rows))

    def test_catalog_accepts_new_languages(self):
        self.catalog.add("NewLanguage", "https://example.org/docs")
        self.assertEqual(self.catalog.list()[0]["name"], "NewLanguage")
        self.catalog.record_verified_exercise("NewLanguage")
        self.assertEqual(self.catalog.list()[0]["verified_exercises"], 1)

    def test_disallows_untrusted_url_schemes(self):
        for url in ("file:///etc/passwd", "http://example.org", "javascript:alert(1)"):
            with self.assertRaises(ValueError):
                self.catalog.add("Bad", url)


if __name__ == "__main__":
    unittest.main()
