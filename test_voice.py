import tempfile
import unittest
from pathlib import Path
from jarvis.voice import VoiceInput


class VoiceTests(unittest.TestCase):
    def test_requires_model_directory(self):
        with self.assertRaises(FileNotFoundError):
            VoiceInput('/unlikely-to-exist-jarvis-vosk-model')

    def test_invalid_sample_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                VoiceInput(folder, sample_rate=0)

    def test_no_audio_dependencies_needed_for_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            obj = VoiceInput(folder)
            self.assertEqual(obj.sample_rate, 16000)
            self.assertEqual(obj.model_path, str(Path(folder)))


if __name__ == '__main__':
    unittest.main()
