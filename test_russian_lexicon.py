import json
import tempfile
import unittest
from pathlib import Path
from jarvis.russian_lexicon import validate_entry, load_lexicon, annotate_stress


class RussianLexiconTests(unittest.TestCase):
    def test_verified_stress_annotation(self):
        lexicon = {"звонит": validate_entry(
            {"word": "звонит", "pronunciation": "звони\u0301т",
             "source": "manual orthoepic review"})}
        self.assertEqual(annotate_stress("Он звонит. Звонит!", lexicon),
                         "Он звони\u0301т. Звони\u0301т!")
        self.assertEqual(annotate_stress("Перезвонит", lexicon), "Перезвонит")

    def test_rejects_unsupported_accent(self):
        with self.assertRaises(ValueError):
            validate_entry({"word": "звонит", "pronunciation": "звонит", "source": "manual"})
        with self.assertRaises(ValueError):
            validate_entry({"word": "звонит", "pronunciation": "зво\u0301нит", "source": ""})

    def test_load_rejects_duplicates(self):
        entry = {"word": "звонит", "pronunciation": "звони\u0301т", "source": "manual"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lexicon.json"
            path.write_text(json.dumps([entry, entry], ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_lexicon(path)


if __name__ == "__main__":
    unittest.main()
