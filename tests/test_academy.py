"""Offline tests for the JARVIS Academy curriculum and source boundaries."""
import tempfile
import unittest
from pathlib import Path

from jarvis.academy import Academy, SKILLS


class AcademyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.academy = Academy(str(Path(self.temp.name) / "academy.db"))

    def tearDown(self):
        self.academy.close()
        self.temp.cleanup()

    def test_official_sources_only(self):
        allowed = (
            ("https://developer.wordpress.org/themes/", "wordpress"),
            ("https://manual.joomla.org/", "joomla"),
            ("https://docs.opencart.com/", "opencart"),
            ("https://developer.mozilla.org/en-US/docs/Web", "web"),
        )
        for url, skill in allowed:
            self.assertEqual(self.academy.check_url(url, skill), url)
        for url in (
            "http://developer.wordpress.org/themes/",
            "https://developer.wordpress.org.attacker.example/",
            "https://127.0.0.1/private",
            "file:///etc/passwd",
            "https://developer.wordpress.org:8080/",
            "https://user:pass@developer.wordpress.org/",
        ):
            with self.assertRaises(ValueError):
                self.academy.check_url(url, "wordpress")

    def test_progress_is_evidence_based(self):
        self.assertEqual(self.academy.progress()["joomla"]["passed"], 0)
        self.academy.record_exercise("joomla", True)
        self.academy.record_exercise("joomla", False)
        self.assertEqual(self.academy.progress()["joomla"], {"completed": 2, "passed": 1})
        self.assertTrue({"wordpress", "joomla", "opencart", "web"}.issubset(SKILLS))

    def test_unreviewed_sources_not_used_as_facts(self):
        self.academy.db.execute(
            "INSERT INTO academy_sources(url,skill,title,excerpt,fetched_at) VALUES(?,?,?,?,?)",
            ("https://developer.wordpress.org/themes/", "wordpress", "Theme docs",
             "External material is untrusted", "2026-01-01"))
        self.academy.db.commit()
        self.assertEqual(self.academy.study_notes("wordpress"), [])
        self.assertEqual(len(self.academy.study_notes("wordpress", reviewed_only=False)), 1)
        self.academy.review("https://developer.wordpress.org/themes/")
        self.assertEqual(len(self.academy.study_notes("wordpress")), 1)


if __name__ == "__main__":
    unittest.main()
