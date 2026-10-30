"""Lightweight, explainable headline classification. No network or model calls."""
import re

TOPICS = {
    "security": ("security", "vulnerability", "cve-", "patch", "exploit", "безопасност"),
    "ai": ("machine learning", "neural", "llm", "artificial intelligence", "transformer", "нейросет", "искусственн"),
    "python": ("python", "cpython", "pip ", "pytorch", "release", "релиз"),
}

def classify(title, url=""):
    """Return a topic or irrelevant; URL is used only for trusted project context."""
    text = title.casefold()
    for category in ("security", "ai", "python"):
        if any(token in text for token in TOPICS[category]):
            return category
    if re.search(r"^https://github\.com/python/cpython/releases/(?:tag/|expanded_assets/)", url):
        return "python"
    return "irrelevant"
