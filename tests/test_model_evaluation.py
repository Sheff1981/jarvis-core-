import unittest

from jarvis.model_evaluation import evaluate_cases, eligible


class ModelEvaluationTests(unittest.TestCase):
    def test_perfect_cases(self):
        result = evaluate_cases(lambda x: x * 2, [(x, x * 2) for x in range(12)])
        self.assertTrue(eligible(result))
        self.assertEqual(result.errors, 0)

    def test_insufficient_cases(self):
        self.assertFalse(eligible(evaluate_cases(lambda x: x, [(1, 1)])))

    def test_predictor_exception_rejected(self):
        def fail(_):
            raise RuntimeError("inference failed")
        result = evaluate_cases(fail, [(x, x) for x in range(12)])
        self.assertEqual(result.errors, 12)
        self.assertFalse(eligible(result))

    def test_low_accuracy_rejected(self):
        result = evaluate_cases(lambda x: 0, [(x, x) for x in range(20)])
        self.assertFalse(eligible(result))


if __name__ == "__main__":
    unittest.main()
