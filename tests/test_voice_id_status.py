"""Unit tests for privacy-safe Voice ID status snapshots."""
import unittest

from jarvis.speaker_gate import SpeakerGate
from jarvis.voice_id_status import snapshot
from jarvis.voice_id_worker import VoiceIDWorker


class VoiceIDStatusTests(unittest.TestCase):
    def test_idle_and_stopped(self):
        worker = VoiceIDWorker(
            SpeakerGate(checker=lambda pcm, rate: True, enabled=True),
            lambda: None, lambda text: None)
        self.assertEqual(snapshot(worker).state, "idle")
        worker.stop()
        self.assertEqual(snapshot(worker).state, "stopped")

    def test_overflow_reports_recovery(self):
        worker = VoiceIDWorker(
            SpeakerGate(checker=lambda pcm, rate: True, enabled=True),
            lambda: None, lambda text: None, queue_size=2)
        worker.submit(bytes(640))
        worker.submit(bytes(640))
        worker.submit(bytes(640))
        status = snapshot(worker)
        self.assertEqual(status.state, "recovering")
        self.assertEqual(status.dropped, 1)
        self.assertEqual(status.generation, 1)


if __name__ == "__main__":
    unittest.main()
