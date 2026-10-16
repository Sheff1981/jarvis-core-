import tempfile
import unittest
from pathlib import Path
from jarvis.dialogue_benchmark import evaluate, write_report


class DialogueBenchmarkTests(unittest.TestCase):
    def test_perfect_responses(self):
        answers = iter(("Привет", "Саша", "Понял", "Исправлено", "JARVIS", "Хорошо", "В пятницу"))
        result = evaluate(lambda _: next(answers))
        self.assertEqual(result["passed"], 3)
        self.assertFalse(result["weight_training_performed"])

    def test_empty_answer_is_failure(self):
        result = evaluate(lambda _: "")
        self.assertEqual(result["passed"], 0)
        self.assertTrue(all(row["error"] == "ValueError" for row in result["results"]))

    def test_report_contains_no_raw_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_report(evaluate(lambda _: "Нет данных"), path)
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("Привет, меня зовут", content)
            self.assertIn('"weight_training_performed": false', content)


if __name__ == "__main__":
    unittest.main()
