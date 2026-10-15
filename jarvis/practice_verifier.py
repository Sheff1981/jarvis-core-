"""Deterministic, offline practice checks. No dynamic code execution."""
import hashlib


class PracticeVerifier:
    """Validate fixed educational exercises without eval, exec or subprocess."""

    @staticmethod
    def verify(exercise, answer):
        if not isinstance(exercise, str) or not isinstance(answer, str):
            raise ValueError("Exercise and answer must be strings")
        if len(answer) > 2000:
            raise ValueError("Answer exceeds practice budget")
        tasks = {
            "python-list-slice": "[2, 3]",
            "python-bool": "True",
            "math-prime": "29",
        }
        if exercise not in tasks:
            raise ValueError("Unknown approved exercise")
        expected = tasks[exercise]
        passed = answer.strip() == expected
        evidence = hashlib.sha256(
            (exercise + "\\0" + answer.strip()).encode("utf-8")).hexdigest()
        return {"exercise": exercise, "passed": passed, "evidence_sha256": evidence}
