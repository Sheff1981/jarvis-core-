"""Offline microphone transcription with actual capture shutdown on mute."""
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
        """Close input stream while gated; reset recognizer on each restart."""
        import sounddevice as sd
        from vosk import Model, KaldiRecognizer

        model = Model(self.model_path)
        while not stop_event.is_set():
            if should_listen is not None and not should_listen():
                stop_event.wait(0.1)
                continue

            recognizer = KaldiRecognizer(model, self.sample_rate)

            def callback(indata, frames, time_info, status):
                if stop_event.is_set() or (
                    should_listen is not None and not should_listen()
                ):
                    raise sd.CallbackStop()
                if recognizer.AcceptWaveform(bytes(indata)):
                    phrase = json.loads(recognizer.Result()).get("text", "").strip()
                    if phrase and not stop_event.is_set() and (
                        should_listen is None or should_listen()
                    ):
                        on_text(phrase)

            with sd.RawInputStream(
                samplerate=self.sample_rate, blocksize=8000,
                dtype="int16", channels=1, callback=callback
            ) as stream:
                while not stop_event.wait(0.1):
                    if should_listen is not None and not should_listen():
                        stream.stop()
                        break
