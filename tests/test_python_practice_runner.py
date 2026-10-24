"""Exercise runner behavior and explicit approval boundary."""
import unittest
from jarvis.python_practice_runner import PythonPracticeRunner


class PythonPracticeRunnerTests(unittest.TestCase):
    def test_owner_approval_required(self):
        with self.assertRaises(PermissionError):
            PythonPracticeRunner().run("def add(a,b): return a+b", "import unittest")

    def test_valid_solution_passes(self):
        source = "def add(a, b):\n    return a + b\n"
        tests = ("import unittest\nfrom solution import add\n"
                 "class Tests(unittest.TestCase):\n"
                 "    def test_add(self): self.assertEqual(add(2,3),5)\n")
        result = PythonPracticeRunner().run(source, tests, owner_approved=True)
        self.assertTrue(result.passed, result.output)
        self.assertEqual(result.tests_run, 1)

    def test_failing_solution_does_not_pass(self):
        source = "def add(a,b): return a-b"
        tests = ("import unittest\nfrom solution import add\n"
                 "class Tests(unittest.TestCase):\n"
                 "    def test_add(self): self.assertEqual(add(2,3),5)\n")
        result = PythonPracticeRunner().run(source, tests, owner_approved=True)
        self.assertFalse(result.passed)

    def test_empty_test_suite_cannot_pass(self):
        result = PythonPracticeRunner().run("x=1", "import unittest",
                                            owner_approved=True)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
