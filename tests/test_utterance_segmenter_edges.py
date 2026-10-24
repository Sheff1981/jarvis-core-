"""Speech segmentation input validation and edge-case regression tests."""
import unittest

from jarvis.utterance_segmenter import UtteranceSegmenter


class SegmenterValidationTests(unittest.TestCase):
    def test_rejects_misaligned_audio(self):
        seg = UtteranceSegmenter(lambda frame: True)
        with self.assertRaises(ValueError):
            seg.push(b"\x00")

    def test_rejects_invalid_configuration(self):
        with self.assertRaises(ValueError):
            UtteranceSegmenter(lambda frame: True, start_frames=0)
        with self.assertRaises(ValueError):
            UtteranceSegmenter(lambda frame: True, end_frames=0)
        with self.assertRaises(ValueError):
            UtteranceSegmenter(lambda frame: True, max_seconds=0)

    def test_fragmented_pcm_frames(self):
        seg = UtteranceSegmenter(lambda frame: any(frame))
        speech = bytes([1, 0]) * 320
        self.assertEqual(seg.push(speech[:100]), [])
        self.assertEqual(seg.push(speech[100:]), [])
        self.assertEqual(seg.consecutive, 1)

    def test_oversized_utterance_rejected(self):
        seg = UtteranceSegmenter(lambda frame: True, max_seconds=1)
        seg.push(bytes([1, 0]) * 320 * 100)
        self.assertFalse(seg.active)


if __name__ == "__main__":
    unittest.main()
