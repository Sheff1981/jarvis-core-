"""Pre-ASR pipeline regression tests using deterministic fake audio."""
import json
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from jarvis.speaker_gate import SpeakerGate
from jarvis.utterance_segmenter import UtteranceSegmenter
from jarvis.voice import VoiceInput


class PreASRTests(unittest.TestCase):
    def test_segments_full_phrase(self):
        seg = UtteranceSegmenter(lambda frame: any(frame))
        samples = [bytes(640)] * 5 + [bytes([1, 0]) * 320] * 15 + [bytes(640)] * 25
        result = []
        for frame in samples:
            result.extend(seg.push(frame))
        self.assertEqual(len(result), 1)
        self.assertGreater(len(result[0]), 16000)

    def test_silence_produces_no_phrase(self):
        seg = UtteranceSegmenter(lambda frame: False)
        self.assertEqual(seg.push(bytes(64000)), [])

    def test_gate_before_recognizer_receives_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            stop = threading.Event()
            events = []
            vosk_calls = []
            class FakeRecognizer:
                def __init__(self, model, rate):
                    self.chunks = []
                def AcceptWaveform(self, chunk):
                    vosk_calls.append(len(chunk))
                    self.chunks.append(chunk)
                    return True
                def FinalResult(self):
                    return json.dumps({"text": "джарвис привет"})
            class FakeStream:
                active = True
                def __init__(self, callback):
                    self.callback = callback
                def __enter__(self):
                    for frame in ([bytes([1, 0]) * 320] * 15 + [bytes(640)] * 25):
                        self.callback(frame, 320, None, None)
                    stop.set()
                    return self
                def __exit__(self, *args):
                    self.active = False
            fake_vosk = types.SimpleNamespace(Model=lambda path: object(),
                                               KaldiRecognizer=FakeRecognizer)
            fake_sd = types.SimpleNamespace(CallbackStop=type("CallbackStop", (Exception,), {}),
                                            RawInputStream=lambda **kwargs: FakeStream(kwargs["callback"]))
            voice = VoiceInput(directory, speaker_gate=SpeakerGate(checker=lambda pcm, rate: False,
                               enabled=True), pre_asr_voice_id=True)
            with patch.dict(sys.modules, {"vosk": fake_vosk, "sounddevice": fake_sd}):
                voice.listen(events.append, stop)
            self.assertEqual(events, [])
            self.assertEqual(vosk_calls, [])

    def test_requires_enabled_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                VoiceInput(directory, pre_asr_voice_id=True)


if __name__ == "__main__":
    unittest.main()
