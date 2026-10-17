"""Speaker gate must never authorize unknown or unverifiable voices."""
import unittest
from jarvis.speaker_gate import SpeakerGate


class SpeakerGateTests(unittest.TestCase):
    def test_disabled_gate_preserves_existing_behavior(self):
        self.assertTrue(SpeakerGate().verify(b"").accepted)

    def test_enabled_without_enrollment_denies(self):
        self.assertFalse(SpeakerGate(enabled=True).verify(bytes(3200)).accepted)

    def test_owner_match_accepts(self):
        gate = SpeakerGate(checker=lambda pcm, rate: True, enabled=True)
        self.assertTrue(gate.verify(bytes(3200)).accepted)

    def test_other_voice_denied(self):
        gate = SpeakerGate(checker=lambda pcm, rate: False, enabled=True)
        self.assertFalse(gate.verify(bytes(3200)).accepted)

    def test_checker_crash_denies(self):
        def broken(pcm, rate):
            raise RuntimeError("no model")
        gate = SpeakerGate(checker=broken, enabled=True)
        self.assertFalse(gate.verify(bytes(3200)).accepted)

    def test_invalid_checker_result_denies(self):
        gate = SpeakerGate(checker=lambda pcm, rate: 1, enabled=True)
        self.assertFalse(gate.verify(bytes(3200)).accepted)

    def test_invalid_audio_denies(self):
        gate = SpeakerGate(checker=lambda pcm, rate: True, enabled=True)
        self.assertFalse(gate.verify(b"\x00").accepted)
        self.assertFalse(gate.verify(bytes(3200), 44100).accepted)


if __name__ == "__main__":
    unittest.main()
