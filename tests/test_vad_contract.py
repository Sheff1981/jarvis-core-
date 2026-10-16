"""Contract tests for the optional VAD audio interface."""
import unittest

from jarvis.vad import SpeechDetector, validate_pcm16_frame


class VADContractTests(unittest.TestCase):
    def test_valid_pcm16_frame_sizes(self):
        for rate in (8000, 16000, 32000, 48000):
            for duration in (10, 20, 30):
                with self.subTest(rate=rate, duration=duration):
                    validate_pcm16_frame(bytes(rate * duration // 1000 * 2),
                                         rate, duration)

    def test_invalid_frame_size_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_pcm16_frame(bytes(319), 16000, 10)

    def test_invalid_rates_and_durations_are_rejected(self):
        for rate, duration in ((44100, 20), (16000, 25),
                               (True, 20), (16000, True)):
            with self.subTest(rate=rate, duration=duration):
                with self.assertRaises(ValueError):
                    validate_pcm16_frame(bytes(640), rate, duration)

    def test_nonbytes_are_rejected(self):
        with self.assertRaises(TypeError):
            validate_pcm16_frame(bytearray(320), 16000, 10)

    def test_detector_implementation_contract(self):
        class TestDetector(SpeechDetector):
            def is_speech(self, pcm16_frame):
                validate_pcm16_frame(pcm16_frame, 16000, 10)
                return any(pcm16_frame)

        detector = TestDetector()
        self.assertFalse(detector.is_speech(bytes(320)))
        self.assertTrue(detector.is_speech(bytes([1]) + bytes(319)))


if __name__ == "__main__":
    unittest.main()
