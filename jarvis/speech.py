"""Optional offline speech output via Windows SAPI through pyttsx3.

Speech is disabled unless explicitly enabled by the application.
"""
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
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", self.rate)
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
