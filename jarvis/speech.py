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
    def __init__(self, enabled=False, rate=175, backend="sapi",
                 piper_exe=None, voice_model=None,
                 piper_length_scale=1.0, piper_sentence_silence=0.0):
        if backend not in ("sapi", "piper"):
            raise ValueError("Unsupported offline speech backend")
        if not isinstance(piper_length_scale, (int, float)) or not 0.7 <= piper_length_scale <= 1.6:
            raise ValueError("Piper length scale must be between 0.7 and 1.6")
        if not isinstance(piper_sentence_silence, (int, float)) or not 0 <= piper_sentence_silence <= 2:
            raise ValueError("Piper sentence silence must be between 0 and 2 seconds")
        self.enabled = enabled
        self.rate = rate
        self.backend = backend
        self.piper_exe = piper_exe
        self.voice_model = voice_model
        self.piper_length_scale = float(piper_length_scale)
        self.piper_sentence_silence = float(piper_sentence_silence)
        self._engine = None

    def say(self, message):
        if not self.enabled or not message:
            return False
        if self.backend == "piper":
            return self._say_piper(message)
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

    def _say_piper(self, message):
        """Run the explicitly configured local Piper binary; never a shell."""
        import subprocess
        import tempfile
        from pathlib import Path

        binary = Path(self.piper_exe) if self.piper_exe else None
        model = Path(self.voice_model) if self.voice_model else None
        if binary is None or not binary.is_file():
            raise RuntimeError("Файл piper.exe не найден. Проверь параметр --piper-bin.")
        if model is None or model.suffix.lower() != ".onnx" or not model.is_file():
            raise RuntimeError("Модель голоса Piper не найдена. Проверь --piper-voice.")
        if not Path(str(model) + ".json").is_file():
            raise RuntimeError("Отсутствует конфигурация голоса Piper (.onnx.json).")
        try:
            import winsound
            with tempfile.TemporaryDirectory(prefix="jarvis-tts-",
                                               dir=str(model.parent)) as folder:
                wav = Path(folder) / "response.wav"
                command = [
                    str(binary), "--model", str(model),
                    "--config", str(model) + ".json",
                    "--output_file", str(wav),
                    "--length_scale", str(self.piper_length_scale),
                    "--sentence_silence", str(self.piper_sentence_silence),
                ]
                subprocess.run(
                    command, input=(message.strip() + "\n").encode("utf-8"),
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                    timeout=60, check=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if not wav.is_file() or wav.stat().st_size < 44:
                    raise RuntimeError("Piper не создал звуковой файл.")
                winsound.PlaySound(str(wav), winsound.SND_FILENAME)
        except (subprocess.SubprocessError, OSError) as exc:
            raise RuntimeError("Не удалось синтезировать или воспроизвести голос Piper.") from exc
        return True

    def close(self):
        if self._engine is not None:
            self._engine.stop()
            self._engine = None
