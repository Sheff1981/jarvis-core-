"""Offline microphone transcription with actual capture shutdown on mute."""
import json
from pathlib import Path


class VoiceInput:
    def __init__(self, model_path, sample_rate=16000, vad_diagnostics=False):
        path = Path(model_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Vosk model folder not found: {path}")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.model_path = str(path)
        self.sample_rate = sample_rate
        self.vad_diagnostics = bool(vad_diagnostics)
        self.vad_activity_frames = 0
        self.vad_total_frames = 0
        self.vad_error = None

    def listen(self, on_text, stop_event, should_listen=None):
        """Close input stream while gated; reset recognizer on each restart."""
        import sounddevice as sd
        from vosk import Model, KaldiRecognizer

        model = Model(self.model_path)
        # Counters describe only this capture run, never a previous run.
        self.vad_activity_frames = 0
        self.vad_total_frames = 0
        vad = None
        if self.vad_diagnostics:
            try:
                from jarvis.vad import VADStream
                vad = VADStream(sample_rate=self.sample_rate)
            except Exception as exc:
                self.vad_error = str(exc)
        failures = 0
        while not stop_event.is_set():
            if should_listen is not None and not should_listen():
                stop_event.wait(0.1)
                continue

            recognizer = KaldiRecognizer(model, self.sample_rate)
            if vad is not None:
                vad.reset()

            callback_error = []

            def callback(indata, frames, time_info, status):
                nonlocal vad
                if stop_event.is_set() or (
                    should_listen is not None and not should_listen()
                ):
                    raise sd.CallbackStop()
                try:
                    if vad is not None:
                        try:
                            decisions = vad.push(bytes(indata))
                            self.vad_total_frames += len(decisions)
                            self.vad_activity_frames += sum(decisions)
                        except Exception as exc:
                            # Diagnostics must never prevent Vosk transcription.
                            self.vad_error = str(exc)
                            vad = None
                    if recognizer.AcceptWaveform(bytes(indata)):
                        phrase = json.loads(recognizer.Result()).get("text", "").strip()
                        if phrase and not stop_event.is_set() and (
                            should_listen is None or should_listen()
                        ):
                            on_text(phrase)
                except Exception as exc:
                    callback_error.append(exc)
                    raise sd.CallbackStop() from exc

            try:
                with sd.RawInputStream(
                    samplerate=self.sample_rate, blocksize=8000,
                    dtype="int16", channels=1, callback=callback
                ) as stream:
                    failures = 0
                    while not stop_event.wait(0.1):
                        if callback_error:
                            raise RuntimeError("Ошибка распознавания аудио") from callback_error[0]
                        if not getattr(stream, "active", True):
                            raise OSError("Аудиопоток неожиданно остановился")
                        if should_listen is not None and not should_listen():
                            stream.stop()
                            break
            except (OSError, RuntimeError) as exc:
                if stop_event.is_set():
                    break
                failures += 1
                if failures >= 3:
                    raise RuntimeError(
                        "Микрофон недоступен после 3 попыток подключения"
                    ) from exc
                if stop_event.wait(0.5 * failures):
                    break
