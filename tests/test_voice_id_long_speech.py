"""Overlong audio must never be re-armed mid-utterance."""
import unittest

from jarvis.utterance_segmenter import UtteranceSegmenter


class LongSpeechTests(unittest.TestCase):
    def test_discards_continuous_overlong_speech(self):
        seg = UtteranceSegmenter(lambda frame: any(frame), max_seconds=1)
        speech = bytes([1, 0]) * 320
        completed = []
        for _ in range(150):
            completed.extend(seg.push(speech))
        self.assertEqual(completed, [])
        self.assertEqual(seg.dropped_utterances, 1)
        self.assertTrue(seg.discard_until_silence)
        for _ in range(25):
            completed.extend(seg.push(bytes(640)))
        self.assertEqual(completed, [])
        self.assertFalse(seg.discard_until_silence)

    def test_accepts_new_phrase_after_silence(self):
        seg = UtteranceSegmenter(lambda frame: any(frame), max_seconds=1)
        speech = bytes([1, 0]) * 320
        for _ in range(100):
            seg.push(speech)
        for _ in range(25):
            seg.push(bytes(640))
        output = []
        for _ in range(15):
            output.extend(seg.push(speech))
        for _ in range(25):
            output.extend(seg.push(bytes(640)))
        self.assertEqual(len(output), 1)


if __name__ == "__main__":
    unittest.main()
