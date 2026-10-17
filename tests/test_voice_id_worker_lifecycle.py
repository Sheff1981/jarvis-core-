"""Voice ID worker generation and shutdown regression tests."""
import unittest

from jarvis.speaker_gate import SpeakerGate
from jarvis.voice_id_worker import VoiceIDWorker


class WorkerLifecycleTests(unittest.TestCase):
    def worker(self):
        return VoiceIDWorker(
            SpeakerGate(checker=lambda pcm, rate: True, enabled=True),
            lambda: None, lambda value: None, queue_size=2)

    def test_overflow_invalidates_previous_generation(self):
        worker = self.worker()
        self.assertTrue(worker.submit(bytes(640)))
        self.assertTrue(worker.submit(bytes(640)))
        self.assertFalse(worker.submit(bytes(640)))
        self.assertEqual(worker._generation, 1)
        self.assertTrue(worker.invalidated.is_set())
        self.assertFalse(worker.submit(bytes(640)))

    def test_stop_invalidates_queue(self):
        worker = self.worker()
        self.assertTrue(worker.submit(bytes(640)))
        worker.stop()
        self.assertTrue(worker.stop_requested.is_set())
        self.assertTrue(worker.invalidated.is_set())
        self.assertFalse(worker.submit(bytes(640)))

    def test_cannot_start_twice(self):
        worker = self.worker()
        worker.start()
        with self.assertRaises(RuntimeError):
            worker.start()
        worker.stop()


if __name__ == "__main__":
    unittest.main()
