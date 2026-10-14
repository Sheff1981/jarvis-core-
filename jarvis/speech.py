"""Opt-in offline speech output with a Russian Windows SAPI preference.

No speech engine or audio device is opened until say() is called.
"""


def _russian_voice(voice):
    """Detect ru-RU pyttsx3/SAPI voices, including byte-encoded language tags."""
    import re

    values = [getattr(voice, "name", ""), getattr(voice, "id", "")]
    values.extend(getattr(voice, "languages", None) or [])
    for value in values:
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        text = str(value).casefold()
        if re.search(r"(?:^|[^a-z])ru(?:-|_|$)", text):
            return True
        if any(name in text for name in ("russian", "irina", "ирина")):
            return True
    return False


class Speaker:
    def __init__(self, enabled=False, rate=175):
        self.enabled = enabled
        self.rate = rate
        self._engine = None

    def say(self, message):
        if not self.enabled or not message:
            return False
        if self._engine is None:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                russian = next(
                    (voice for voice in engine.getProperty("voices")
                     if _russian_voice(voice)),
                    None,
                )
                if russian is not None:
                    engine.setProperty("voice", russian.id)
                self._engine = engine
            except Exception as exc:
                raise RuntimeError("Не удалось запустить локальный синтез речи.") from exc
        try:
            self._engine.say(message)
            self._engine.runAndWait()
        except Exception as exc:
            raise RuntimeError("Не удалось воспроизвести голосовой ответ.") from exc
        return True

    def close(self):
        if self._engine is not None:
            self._engine.stop()
            self._engine = None
