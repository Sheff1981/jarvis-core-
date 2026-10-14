import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.voice import VoiceInput


class FailingStream:
    attempts = 0

    def __init__(self, **kwargs):
        FailingStream.attempts += 1
        raise OSError("device unavailable")


class RecoveringStream:
    attempts = 0

    def __init__(self, **kwargs):
        RecoveringStream.attempts += 1
        if RecoveringStream.attempts == 1:
            raise OSError("temporary disconnect")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def stop(self):
        pass


class RetryTests(unittest.TestCase):
    def _run(self, stream_type, stop):
        sd = types.SimpleNamespace(RawInputStream=stream_type, CallbackStop=Exception)
        vosk = types.SimpleNamespace(
            Model=lambda path: object(),
            KaldiRecognizer=lambda model, rate: object(),
        )
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(sys.modules, {"sounddevice": sd, "vosk": vosk}):
                VoiceInput(folder).listen(lambda phrase: None, stop)

    def test_fails_after_three_attempts(self):
        FailingStream.attempts = 0
        with self.assertRaisesRegex(RuntimeError, "3 попыток"):
            self._run(FailingStream, threading.Event())
        self.assertEqual(FailingStream.attempts, 3)

    def test_retry_can_be_cancelled(self):
        stop = threading.Event()
        FailingStream.attempts = 0
        timer = threading.Timer(0.1, stop.set)
        timer.start()
        try:
            self._run(FailingStream, stop)
        finally:
            timer.join()
        self.assertEqual(FailingStream.attempts, 1)


if __name__ == "__main__":
    unittest.main()
