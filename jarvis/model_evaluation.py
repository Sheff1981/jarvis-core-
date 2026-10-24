"""Deterministic offline evaluation gate for model candidates."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Evaluation:
    total: int
    passed: int
    errors: int

    @property
    def accuracy(self):
        return self.passed / self.total if self.total else 0.0


def evaluate_cases(predict, cases):
    if not callable(predict):
        raise TypeError("predict must be callable")
    total = passed = errors = 0
    for example, expected in cases:
        total += 1
        try:
            if predict(example) == expected:
                passed += 1
        except Exception:
            errors += 1
    return Evaluation(total, passed, errors)


def eligible(result, min_cases=10, min_accuracy=0.95):
    if min_cases < 1 or not 0 <= min_accuracy <= 1:
        raise ValueError("invalid evaluation policy")
    return (result.total >= min_cases and result.errors == 0
            and result.accuracy >= min_accuracy)
