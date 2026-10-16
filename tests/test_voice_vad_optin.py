"""VAD diagnostics must remain disabled by default and preserve Vosk input."""
import tempfile
import unittest
from pathlib import Path

from jarvis.voice import VoiceInput


class VoiceVADOptInTests(unittest.TestCase):
    def test_default_diagnostics_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            voice = VoiceInput(directory)
            self.assertFalse(voice.vad_diagnostics)
            self.assertEqual(voice.vad_activity_frames, 0)
            self.assertEqual(voice.vad_total_frames, 0)

    def test_explicit_diagnostics_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            voice = VoiceInput(directory, vad_diagnostics=True)
            self.assertTrue(voice.vad_diagnostics)
            self.assertEqual(voice.vad_total_frames, 0)


if __name__ == "__main__":
    unittest.main()
