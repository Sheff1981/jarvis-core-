"""Offline practice verification tests."""
import unittest
from jarvis.practice_verifier import PracticeVerifier


class PracticeVerifierTests(unittest.TestCase):
    def test_pass_and_fail(self):
        self.assertTrue(PracticeVerifier.verify("math-prime", "29")["passed"])
        self.assertFalse(PracticeVerifier.verify("math-prime", "30")["passed"])

    def test_unknown_exercise_rejected(self):
        with self.assertRaises(ValueError):
            PracticeVerifier.verify("download-and-run", "yes")

    def test_bounded_input(self):
        with self.assertRaises(ValueError):
            PracticeVerifier.verify("python-bool", "x" * 2001)


if __name__ == "__main__":
    unittest.main()
