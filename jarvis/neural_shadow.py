"""Opt-in read-only shadow evaluation.

Shadow results are never forwarded as live assistant responses.
"""
from dataclasses import dataclass

from jarvis.model_evaluation import evaluate_cases, eligible


@dataclass(frozen=True)
class ShadowReport:
    total: int
    passed: int
    errors: int
    eligible: bool


def evaluate_shadow(adapter, examples, min_cases=10, min_accuracy=0.95):
    result = evaluate_cases(lambda text: adapter.infer(text).text, examples)
    return ShadowReport(result.total, result.passed, result.errors,
                        eligible(result, min_cases, min_accuracy))
