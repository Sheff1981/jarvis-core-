"""Session-scoped conversation modes; no computer tools are invoked here."""
from enum import Enum


class Mode(str, Enum):
    CONVERSATION = "conversation"
    WORK = "work"


class Session:
    """Explicit mode transitions with no implicit permission grants."""

    def __init__(self):
        self.mode = Mode.CONVERSATION
        self.history = []

    def switch(self, mode):
        target = Mode(mode)
        self.mode = target
        return self.mode

    def append(self, role, message):
        if role not in ("user", "assistant"):
            raise ValueError("Unsupported role")
        if not isinstance(message, str):
            raise TypeError("Message must be text")
        self.history.append((role, message))
        self.history = self.history[-40:]

    def clear(self):
        self.history.clear()
        self.mode = Mode.CONVERSATION
