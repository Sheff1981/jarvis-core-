"""Voice ID offline enrollment tests (no model downloads)."""
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from jarvis_voice_enroll import read_wav, evaluate_scores, cosine
from jarvis.speaker_ecapa import LocalECAPAExtractor
from jarvis.speaker_profile import SpeakerProfileStore


class VoiceIdEnrollmentTests(unittest.TestCase):
    def test_wav_16khz_mono_pcm(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owner.wav"
            with wave.open(str(path), "wb") as file:
                file.setnchannels(1)
                file.setsampwidth(2)
                file.setframerate(16000)
                file.writeframes(bytes(32000))
            self.assertEqual(len(read_wav(path)), 32000)

    def test_wrong_sample_rate_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.wav"
            with wave.open(str(path), "wb") as file:
                file.setnchannels(1)
                file.setsampwidth(2)
                file.setframerate(8000)
                file.writeframes(bytes(16000))
            with self.assertRaises(ValueError):
                read_wav(path)

    def test_calibration_never_accepts_impostors_for_zero_far(self):
        result = evaluate_scores([0.9, 0.85], [0.4, 0.5], target_far=0)
        self.assertEqual(result["false_accepts"], 0)
        self.assertEqual(result["false_rejects"], 0)
        self.assertLessEqual(result["threshold"], 0.85)

    def test_calibration_reports_incompatible_scores(self):
        result = evaluate_scores([0.2], [0.9], target_far=0)
        self.assertEqual(result["false_accepts"], 0)
        self.assertEqual(result["false_rejects"], 1)

    def test_empty_holdout_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_scores([], [0.5])

    def test_cosine_rejects_wrong_embedding_width(self):
        with self.assertRaises(ValueError):
            cosine([1, 0], [1, 0, 0])

    def test_local_model_directory_is_required(self):
        with self.assertRaises(FileNotFoundError):
            LocalECAPAExtractor("/nonexistent-jarvis-ecapa-model")


if __name__ == "__main__":
    unittest.main()
