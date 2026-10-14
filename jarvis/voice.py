"""Offline microphone transcription; muted audio is never sent to recognizer."""
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

    def listen(self, on_text, stop_event, should_listen=None):
        """Read local audio until stopped; gate recognition when muted or speaking."""
        import sounddevice as sd
        from vosk import Model, KaldiRecognizer

        model = Model(self.model_path)
        recognizer = KaldiRecognizer(model, self.sample_rate)
        was_blocked = False

        def callback(indata, frames, time_info, status):
            nonlocal recognizer, was_blocked
            if stop_event.is_set():
                raise sd.CallbackStop()
            if should_listen is not None and not should_listen():
                was_blocked = True
                return
            if was_blocked:
                # Flush recognition state so old partial speech cannot leak.
                recognizer = KaldiRecognizer(model, self.sample_rate)
                was_blocked = False
            if recognizer.AcceptWaveform(bytes(indata)):
                phrase = json.loads(recognizer.Result()).get("text", "").strip()
                if phrase:
                    on_text(phrase)

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               dtype="int16", channels=1, callback=callback):
            while not stop_event.wait(0.2):
                pass
