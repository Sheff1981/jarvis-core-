"""Offline microphone recognition using an explicitly installed Vosk model.

No audio is stored or transmitted. Importing this module does not activate the mic.
"""
import json
from pathlib import Path


class VoiceInput:
    def __init__(self, model_path, sample_rate=16000):
        path = Path(model_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Vosk model folder not found: {path}")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.model_path = str(path)
        self.sample_rate = sample_rate

    def listen(self, on_text, stop_event):
        """Stream finalized recognized phrases until stop_event is set."""
        import sounddevice as sd
        from vosk import Model, KaldiRecognizer

        recognizer = KaldiRecognizer(Model(self.model_path), self.sample_rate)

        def callback(indata, frames, time_info, status):
            if stop_event.is_set():
                raise sd.CallbackStop()
            if recognizer.AcceptWaveform(bytes(indata)):
                phrase = json.loads(recognizer.Result()).get("text", "").strip()
                if phrase:
                    on_text(phrase)

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               dtype="int16", channels=1, callback=callback):
            while not stop_event.wait(0.2):
                pass
