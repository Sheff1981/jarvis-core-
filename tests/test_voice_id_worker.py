"""Tests for the bounded asynchronous Voice ID worker."""
import json
import time
import unittest

from jarvis.speaker_gate import SpeakerGate
from jarvis.voice_id_worker import VoiceIDWorker


class Recognizer:
    def __init__(self, seen):
        self.seen = seen
    def AcceptWaveform(self, audio):
        self.seen.append(audio)
        return True
    def FinalResult(self):
        return json.dumps({"text": "джарвис привет"})


def phrase():
    return [bytes([1, 0]) * 320] * 15 + [bytes(640)] * 25


class VoiceIDWorkerTests(unittest.TestCase):
    def run_phrase(self, accepted):
        heard, seen = [], []
        gate = SpeakerGate(checker=lambda pcm, rate: accepted, enabled=True)
        worker = VoiceIDWorker(gate, lambda: Recognizer(seen), heard.append)
        worker.start()
        for frame in phrase():
            worker.submit(frame)
            time.sleep(0.001)
        for _ in range(100):
            if worker.accepted or worker.rejected or worker.error:
                break
            time.sleep(0.01)
        worker.stop()
        self.assertIsNone(worker.error)
        return heard, seen

    def test_owner_accepted(self):
        heard, seen = self.run_phrase(True)
        self.assertEqual(heard, ["джарвис привет"])
        self.assertEqual(len(seen), 1)

    def test_other_speaker_not_sent_to_asr(self):
        heard, seen = self.run_phrase(False)
        self.assertEqual(heard, [])
        self.assertEqual(seen, [])

    def test_queue_overflow_invalidates_audio(self):
        worker = VoiceIDWorker(SpeakerGate(checker=lambda pcm, rate: True,
                               enabled=True), lambda: Recognizer([]), lambda text: None,
                               queue_size=2)
        self.assertTrue(worker.submit(bytes(640)))
        self.assertTrue(worker.submit(bytes(640)))
        self.assertFalse(worker.submit(bytes(640)))
        self.assertEqual(worker.dropped_chunks, 1)
        self.assertTrue(worker.invalidated.is_set())

    def test_requires_gate(self):
        with self.assertRaises(ValueError):
            VoiceIDWorker(None, lambda: None, lambda text: None)


if __name__ == "__main__":
    unittest.main()
