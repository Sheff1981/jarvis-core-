"""Offline microphone transcription with actual capture shutdown on mute."""
import json
from pathlib import Path


class VoiceInput:
    def __init__(self, model_path, sample_rate=16000, vad_diagnostics=False, speaker_gate=None, pre_asr_voice_id=False):
        path = Path(model_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Vosk model folder not found: {path}")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.model_path = str(path)
        self.sample_rate = sample_rate
        self.vad_diagnostics = bool(vad_diagnostics)
        self.speaker_gate = speaker_gate
        self.pre_asr_voice_id = bool(pre_asr_voice_id)
        if self.pre_asr_voice_id and (speaker_gate is None or not speaker_gate.enabled):
            raise ValueError('pre-ASR Voice ID requires an enabled speaker gate')
        if self.pre_asr_voice_id and sample_rate != 16000:
            raise ValueError('pre-ASR Voice ID requires 16000 Hz')
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
        self.vad_error = None
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
            worker = None
            if self.pre_asr_voice_id:
                from jarvis.voice_id_worker import VoiceIDWorker
                worker = VoiceIDWorker(self.speaker_gate,
                    lambda: KaldiRecognizer(model, self.sample_rate),
                    on_text, sample_rate=self.sample_rate,
                    should_listen=should_listen)
            if vad is not None:
                try:
                    vad.reset()
                except Exception as exc:
                    self.vad_error = str(exc)
                    vad = None

            callback_error = []
            speaker_audio = bytearray()
            speaker_overflow = False
            max_speaker_bytes = self.sample_rate * 2 * 15

            def callback(indata, frames, time_info, status):
                nonlocal vad, speaker_overflow
                if stop_event.is_set() or (
                    should_listen is not None and not should_listen()
                ):
                    raise sd.CallbackStop()
                try:
                    audio = bytes(indata)
                    if vad is not None:
                        try:
                            decisions = vad.push(audio)
                            self.vad_total_frames += len(decisions)
                            self.vad_activity_frames += sum(decisions)
                        except Exception as exc:
                            # Diagnostics must never prevent Vosk transcription.
                            self.vad_error = str(exc)
                            vad = None
                    if worker is not None:
                        worker.submit(audio)
                        return
                    if self.speaker_gate is not None and self.speaker_gate.enabled:
                        if len(speaker_audio) + len(audio) > max_speaker_bytes:
                            speaker_overflow = True
                        else:
                            speaker_audio.extend(audio)
                    if recognizer.AcceptWaveform(audio):
                        phrase = json.loads(recognizer.Result()).get("text", "").strip()
                        speaker_ok = True
                        if self.speaker_gate is not None and self.speaker_gate.enabled:
                            speaker_ok = (not speaker_overflow and
                                          self.speaker_gate.verify(bytes(speaker_audio),
                                                                   self.sample_rate).accepted)
                            speaker_audio.clear()
                            speaker_overflow = False
                        if phrase and speaker_ok and not stop_event.is_set() and (
                            should_listen is None or should_listen()
                        ):
                            on_text(phrase)
                except Exception as exc:
                    callback_error.append(exc)
                    raise sd.CallbackStop() from exc

            try:
                if worker is not None:
                    worker.start()
                with sd.RawInputStream(
                    samplerate=self.sample_rate, blocksize=8000,
                    dtype="int16", channels=1, callback=callback
                ) as stream:
                    failures = 0
                    while not stop_event.wait(0.1):
                        if worker is not None and worker.error is not None:
                            raise RuntimeError('Voice ID worker failed') from worker.error
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
            finally:
                if worker is not None:
                    worker.stop()
