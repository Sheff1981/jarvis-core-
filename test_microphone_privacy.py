import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.voice import VoiceInput


class FakeRecognizer:
    def __init__(self, model, rate):
        self.model = model

    def AcceptWaveform(self, data):
        return False


class FakeStream:
    active = 0
    opened = 0
    closed = 0

    def __init__(self, **kwargs):
        self.callback = kwargs["callback"]

    def __enter__(self):
        FakeStream.active += 1
        FakeStream.opened += 1
        return self

    def stop(self):
        FakeStream.active -= 1

    def __exit__(self, *args):
        if FakeStream.active:
            FakeStream.active -= 1
        FakeStream.closed += 1


class CapturePrivacyTests(unittest.TestCase):
    def test_mute_closes_capture_and_unmute_reopens(self):
        FakeStream.active = FakeStream.opened = FakeStream.closed = 0
        sd = types.SimpleNamespace(RawInputStream=FakeStream, CallbackStop=Exception)
        vosk = types.SimpleNamespace(Model=lambda path: object(), KaldiRecognizer=FakeRecognizer)
        with tempfile.TemporaryDirectory() as folder:
            input_device = VoiceInput(folder)
            stop = threading.Event()
            allowed = threading.Event()
            allowed.set()
            with patch.dict(sys.modules, {"sounddevice": sd, "vosk": vosk}):
                worker = threading.Thread(
                    target=input_device.listen,
                    args=(lambda text: None, stop, allowed.is_set),
                )
                worker.start()
                try:
                    self.assertTrue(self._wait(lambda: FakeStream.opened >= 1))
                    allowed.clear()
                    self.assertTrue(self._wait(lambda: FakeStream.active == 0))
                    allowed.set()
                    self.assertTrue(self._wait(lambda: FakeStream.opened >= 2))
                finally:
                    stop.set()
                    worker.join(timeout=3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(FakeStream.active, 0)

    @staticmethod
    def _wait(predicate):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.02)
        return False


if __name__ == "__main__":
    unittest.main()
