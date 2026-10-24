"""Conservative Russian speech lexicon with explicit accent notation.

Entries are reviewed manually. Dahl is historical vocabulary, not a modern
orthographic or orthoepic authority. No web scraping or model training here.
"""
import json
import re
from pathlib import Path

WORD = re.compile(r"^[А-Яа-яЁё-]{2,64}$")
ACCENTED = re.compile(r"^[А-Яа-яЁё\u0301-]{2,80}$")


def validate_entry(entry):
    if not isinstance(entry, dict):
        raise ValueError("Lexicon entry must be an object")
    word = entry.get("word")
    pronunciation = entry.get("pronunciation")
    source = entry.get("source")
    if not isinstance(word, str) or not WORD.fullmatch(word):
        raise ValueError("Invalid Russian word")
    if not isinstance(pronunciation, str) or not ACCENTED.fullmatch(pronunciation):
        raise ValueError("Invalid pronunciation")
    if not isinstance(source, str) or not source.strip() or len(source) > 200:
        raise ValueError("Missing provenance")
    normalized = pronunciation.replace("\u0301", "").casefold()
    if normalized != word.casefold():
        raise ValueError("Pronunciation must preserve the written word")
    if pronunciation.count("\u0301") != 1:
        raise ValueError("Exactly one marked stress is required")
    return {"word": word, "pronunciation": pronunciation, "source": source.strip()}


def load_lexicon(path):
    """Load a small explicitly reviewed JSON lexicon, rejecting duplicates."""
    path = Path(path)
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Lexicon too large")
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("Lexicon must be an array")
    lexicon = {}
    for raw in entries:
        entry = validate_entry(raw)
        key = entry["word"].casefold()
        if key in lexicon:
            raise ValueError("Duplicate word")
        lexicon[key] = entry
    return lexicon


def annotate_stress(text, lexicon):
    """Add stress marks to exact word matches without guessing morphology."""
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError("Invalid text")
    if not isinstance(lexicon, dict):
        raise TypeError("Invalid lexicon")
    def replace(match):
        word = match.group()
        entry = lexicon.get(word.casefold())
        if not entry:
            return word
        pronunciation = entry["pronunciation"]
        return pronunciation.upper() if word.isupper() else (
            pronunciation[0].upper() + pronunciation[1:] if word[0].isupper()
            else pronunciation)
    return re.sub(r"[А-Яа-яЁё]+", replace, text)
