"""Conservative Russian wake phrase gate. No network and no microphone access."""
import re


def extract_command(phrase):
    """Return (activated, command). The caller decides whether to respond."""
    normalized = re.sub(r"[!?.,:;]+", " ", phrase.casefold()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    names = ("джарвис", "джервис", "jarvis")
    for name in names:
        if normalized == name or normalized == "привет " + name:
            return True, "привет"
        if normalized.startswith(name + " "):
            command = normalized[len(name):].strip()
            return True, command if command else "привет"
        if normalized.startswith("привет " + name + " "):
            return True, normalized[len("привет " + name):].strip()
    return False, ""
