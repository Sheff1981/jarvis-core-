"""Incremental sentence segmentation for text-to-speech."""
import re

_END = re.compile(r'[.!?…]+[»)]*(?=\s|$)')


class SpeechChunker:
    def __init__(self, max_chars=220):
        if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 30:
            raise ValueError("max_chars must be at least 30")
        self.max_chars = max_chars
        self._buffer = ""

    def feed(self, text):
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        self._buffer += text
        ready = []
        while self._buffer:
            match = _END.search(self._buffer)
            if match and match.end() <= self.max_chars:
                cut = match.end()
            elif len(self._buffer) >= self.max_chars:
                boundary = self._buffer.rfind(" ", 0, self.max_chars + 1)
                cut = boundary if boundary > 0 else self.max_chars
            else:
                break
            piece = self._buffer[:cut].strip()
            self._buffer = self._buffer[cut:].lstrip()
            if piece:
                ready.append(piece)
        return ready

    def flush(self):
        remaining = self._buffer.strip()
        self._buffer = ""
        return [remaining] if remaining else []
