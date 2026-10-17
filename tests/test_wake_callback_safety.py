"""Regression tests for non-blocking microphone callbacks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WakeCallbackSafetyTests(unittest.TestCase):
    def test_unified_launcher_dispatches_off_audio_thread(self):
        code = (ROOT / "jarvis_launcher.py").read_text(encoding="utf-8")
        self.assertIn("queue.Queue(maxsize=8)", code)
        self.assertIn("voice.listen(enqueue, stop)", code)
        self.assertIn("wake.handle(phrase)", code)
        self.assertNotIn("voice.listen(wake.handle, stop)", code)

    def test_standalone_listener_dispatches_off_audio_thread(self):
        code = (ROOT / "wake_cli.py").read_text(encoding="utf-8")
        self.assertIn("queue.Queue(maxsize=8)", code)
        self.assertIn("VoiceInput(args.vosk_model).listen(enqueue, stop)", code)
        self.assertNotIn("VoiceInput(args.vosk_model).listen(dispatcher.handle, stop)", code)


if __name__ == "__main__":
    unittest.main()
