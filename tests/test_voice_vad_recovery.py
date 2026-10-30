"""Verify a failing optional VAD cannot block Vosk recognition."""
import json
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from jarvis.voice import VoiceInput
from jarvis.speaker_gate import SpeakerGate


class FailingVAD:
    def __init__(self, **kwargs):
        self.calls = 0

    def reset(self):
        pass

    def push(self, audio):
        self.calls += 1
        raise RuntimeError("simulated VAD failure")


class ResetFailingVAD(FailingVAD):
    def reset(self):
        raise RuntimeError("simulated VAD reset failure")


class FakeRecognizer:
    def __init__(self, model, rate):
        self.received = []

    def AcceptWaveform(self, audio):
        self.received.append(audio)
        return True

    def Result(self):
        return json.dumps({"text": "проверка микрофона"})


class FakeStream:
    def __init__(self, callback, stop_event):
        self.callback = callback
        self.stop_event = stop_event
        self.active = True

    def __enter__(self):
        self.callback(bytes(8000), 4000, None, None)
        self.stop_event.set()
        return self

    def __exit__(self, *args):
        self.active = False


class VoiceVADRecoveryTests(unittest.TestCase):
    def test_unknown_speaker_does_not_reach_assistant(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            heard = []
            voice = VoiceInput(directory, speaker_gate=SpeakerGate(enabled=True))
            fake_vosk = types.SimpleNamespace(
                Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(
                CallbackStop=type("CallbackStop", (Exception,), {}),
                RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"], stop))
            with patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}):
                voice.listen(heard.append, stop)
            self.assertEqual(heard, [])

    def test_verified_owner_reaches_assistant(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            heard = []
            seen = []
            def verify(pcm, rate):
                seen.append((len(pcm), rate))
                return True
            voice = VoiceInput(directory, speaker_gate=SpeakerGate(
                checker=verify, enabled=True))
            fake_vosk = types.SimpleNamespace(
                Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(
                CallbackStop=type("CallbackStop", (Exception,), {}),
                RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"], stop))
            with patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}):
                voice.listen(heard.append, stop)
            self.assertEqual(heard, ["проверка микрофона"])
            self.assertEqual(seen, [(8000, 16000)])

    def test_vad_reset_failure_preserves_vosk_recognition(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            heard = []
            voice = VoiceInput(directory, vad_diagnostics=True)
            fake_vosk = types.SimpleNamespace(
                Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(
                CallbackStop=type("CallbackStop", (Exception,), {}),
                RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"], stop))
            with (patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}),
                  patch("jarvis.vad.VADStream", ResetFailingVAD)):
                voice.listen(heard.append, stop)
            self.assertEqual(heard, ["проверка микрофона"])
            self.assertEqual(voice.vad_error, "simulated VAD reset failure")

    def test_vad_setup_failure_preserves_vosk_recognition(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            heard = []
            voice = VoiceInput(directory, vad_diagnostics=True)
            fake_vosk = types.SimpleNamespace(
                Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(
                CallbackStop=type("CallbackStop", (Exception,), {}),
                RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"], stop))
            with (patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}),
                  patch("jarvis.vad.VADStream", side_effect=RuntimeError("VAD unavailable"))):
                voice.listen(heard.append, stop)
            self.assertEqual(heard, ["проверка микрофона"])
            self.assertEqual(voice.vad_error, "VAD unavailable")

    def test_vad_crash_preserves_vosk_recognition(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            heard = []
            voice = VoiceInput(directory, vad_diagnostics=True)
            fake_vosk = types.SimpleNamespace(
                Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(
                CallbackStop=type("CallbackStop", (Exception,), {}),
                RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"], stop))
            with (patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}),
                  patch("jarvis.vad.VADStream", FailingVAD)):
                voice.listen(heard.append, stop)
            self.assertEqual(heard, ["проверка микрофона"])
            self.assertEqual(voice.vad_error, "simulated VAD failure")
            self.assertEqual(voice.vad_total_frames, 0)


if __name__ == "__main__":
    unittest.main()
