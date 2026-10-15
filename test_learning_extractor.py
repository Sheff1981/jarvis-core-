import unittest
from jarvis.learning_extractor import extract_excerpt, MAX_HTML

class ExtractorTests(unittest.TestCase):
    def test_extracts_article_and_ignores_scripts(self):
        data = b"<html><script>SECRET</script><p>" + b"Python release notes explain compatibility and security changes for this release in detail." + b"</p></html>"
        result = extract_excerpt(data)
        self.assertIn("Python release notes", result)
        self.assertNotIn("SECRET", result)

    def test_rejects_large_page(self):
        with self.assertRaises(ValueError):
            extract_excerpt(b"x" * (MAX_HTML + 1))
