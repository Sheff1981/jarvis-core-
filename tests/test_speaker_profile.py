"""Local speaker enrollment, matching and deletion contract tests."""
import tempfile
import unittest
from pathlib import Path

from jarvis.speaker_profile import SpeakerProfileStore, CosineSpeakerVerifier
from jarvis.speaker_gate import SpeakerGate


class SpeakerProfileTests(unittest.TestCase):
    def test_enrollment_match_mismatch_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SpeakerProfileStore(Path(directory) / "private" / "owner.json")
            store.enroll([[1, 0, 0], [0.9, 0.1, 0], [1, 0.1, 0]], "test-model-v1")
            self.assertEqual(len(store.load("test-model-v1")), 3)
            owner = CosineSpeakerVerifier(store, lambda pcm, rate: [1, 0, 0], "test-model-v1")
            other = CosineSpeakerVerifier(store, lambda pcm, rate: [0, 1, 0], "test-model-v1")
            self.assertTrue(SpeakerGate(owner, enabled=True).verify(bytes(3200)).accepted)
            self.assertFalse(SpeakerGate(other, enabled=True).verify(bytes(3200)).accepted)
            store.delete()
            self.assertFalse(SpeakerGate(owner, enabled=True).verify(bytes(3200)).accepted)

    def test_rejects_insufficient_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SpeakerProfileStore(Path(directory) / "owner.json")
            with self.assertRaises(ValueError):
                store.enroll([[1, 0], [1, 0]], "test-model-v1")

    def test_rejects_invalid_embeddings(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SpeakerProfileStore(Path(directory) / "owner.json")
            with self.assertRaises(ValueError):
                store.enroll([[1, 0], [float("nan"), 1], [1, 0]], "test-model-v1")
            with self.assertRaises(ValueError):
                store.enroll([[1, 0], [1, 0, 0], [1, 0]], "test-model-v1")

    def test_model_mismatch_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SpeakerProfileStore(Path(directory) / "owner.json")
            store.enroll([[1, 0], [1, 0], [1, 0]], "model-a")
            verifier = CosineSpeakerVerifier(store, lambda pcm, rate: [1, 0], "model-b")
            self.assertFalse(SpeakerGate(verifier, enabled=True).verify(bytes(3200)).accepted)


if __name__ == "__main__":
    unittest.main()
