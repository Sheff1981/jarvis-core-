"""Offline dialogue benchmark for a locally hosted JARVIS model.

This module evaluates responses; it does not train model weights.
"""
import json
from pathlib import Path

CASES = (
    {"id": "greeting", "turns": ["Привет, меня зовут Саша.", "Как меня зовут?"],
     "required": ("саша", "александр")},
    {"id": "correction", "turns": ["Мой проект называется Лизория.", "Исправление: название проекта JARVIS.", "Как называется проект?"],
     "required": ("jarvis",)},
    {"id": "clarification", "turns": ["Запомни, что встреча в пятницу.", "В какой день встреча?"],
     "required": ("пятниц",)},
)


def evaluate(ask, reset=None):
    """Run a deterministic smoke benchmark against an injected chat callable."""
    if not callable(ask):
        raise TypeError("ask must be callable")
    if reset is not None and not callable(reset):
        raise TypeError("reset must be callable")
    results = []
    for case in CASES:
        replies = []
        error = None
        try:
            if reset is not None:
                reset()
            for turn in case["turns"]:
                reply = ask(turn)
                if not isinstance(reply, str) or not reply.strip():
                    raise ValueError("Empty model reply")
                replies.append(reply[:2000])
        except Exception as exc:
            error = type(exc).__name__
        final = replies[-1].casefold() if len(replies) == len(case["turns"]) else ""
        passed = error is None and any(word in final for word in case["required"])
        results.append({"id": case["id"], "passed": passed, "error": error})
    return {"total": len(results), "passed": sum(item["passed"] for item in results),
            "results": results, "weight_training_performed": False}


def write_report(report, path):
    """Persist aggregate benchmark results without storing personal dialogue."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def evaluate_local(model="qwen3:1.7b", *, cpu_only=True, timeout=45):
    """Run real offline Ollama dialogue tests; no external API or weight changes."""
    from jarvis.local_llm import LocalLLM
    llm = LocalLLM(model=model, cpu_only=cpu_only, timeout=timeout,
                   max_turns=4, think=False)
    llm.mode = "chat"
    return evaluate(llm.ask, reset=llm.clear_history)
