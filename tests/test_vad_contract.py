"""Contract tests for the optional VAD audio interface."""
import unittest

from jarvis.vad import EnergyVAD, SpeechDetector, validate_pcm16_frame


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

    def test_vad_stream_emits_per_frame_activity(self):
        import struct
        from jarvis.vad import VADStream
        stream = VADStream(start_frames=2, stop_frames=2)
        loud = struct.pack("<320h", *([1200] * 320))
        quiet = bytes(640)
        self.assertEqual(stream.push(loud[:200]), [])
        self.assertEqual(stream.push(loud[200:]), [False])
        self.assertEqual(stream.push(loud), [True])
        self.assertEqual(stream.push(quiet), [True])
        self.assertEqual(stream.push(quiet), [False])

    def test_vad_stream_reset_clears_pending_and_activity(self):
        import struct
        from jarvis.vad import VADStream
        stream = VADStream(start_frames=1, stop_frames=2)
        loud = struct.pack("<320h", *([1200] * 320))
        self.assertEqual(stream.push(loud), [True])
        stream.push(bytes(100))
        stream.reset()
        self.assertEqual(stream.push(bytes(640)), [False])

    def test_activity_tracker_requires_sustained_sound(self):
        from jarvis.vad import SpeechActivityTracker
        tracker = SpeechActivityTracker(start_frames=2, stop_frames=3)
        self.assertFalse(tracker.update(True))
        self.assertFalse(tracker.update(False))
        self.assertFalse(tracker.update(True))
        self.assertTrue(tracker.update(True))
        self.assertTrue(tracker.update(False))
        self.assertTrue(tracker.update(False))
        self.assertFalse(tracker.update(False))

    def test_activity_tracker_reset(self):
        from jarvis.vad import SpeechActivityTracker
        tracker = SpeechActivityTracker(start_frames=1, stop_frames=2)
        self.assertTrue(tracker.update(True))
        tracker.reset()
        self.assertFalse(tracker.active)
        self.assertFalse(tracker.update(False))

    def test_activity_tracker_invalid_configuration(self):
        from jarvis.vad import SpeechActivityTracker
        for kwargs in ({"start_frames": 0}, {"stop_frames": 0},
                       {"start_frames": True}, {"stop_frames": 1.5}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    SpeechActivityTracker(**kwargs)
        with self.assertRaises(TypeError):
            SpeechActivityTracker().update(1)

    def test_audio_frame_buffer_split_chunks(self):
        from jarvis.vad import AudioFrameBuffer
        buffer = AudioFrameBuffer()
        self.assertEqual(buffer.push(bytes(200)), [])
        self.assertEqual(buffer.pending_bytes, 200)
        self.assertEqual(buffer.push(bytes(1080)), [bytes(640), bytes(640)])
        self.assertEqual(buffer.pending_bytes, 0)

    def test_audio_frame_buffer_reset_discards_partial_frame(self):
        from jarvis.vad import AudioFrameBuffer
        buffer = AudioFrameBuffer()
        buffer.push(bytes(320))
        buffer.reset()
        self.assertEqual(buffer.pending_bytes, 0)
        self.assertEqual(buffer.push(bytes(640)), [bytes(640)])

    def test_audio_frame_buffer_rejects_partial_pcm_sample(self):
        from jarvis.vad import AudioFrameBuffer
        buffer = AudioFrameBuffer()
        with self.assertRaises(ValueError):
            buffer.push(bytes(3))
        self.assertEqual(buffer.pending_bytes, 0)

    def test_energy_vad_silence_and_loud_audio(self):
        import struct
        vad = EnergyVAD(threshold=500)
        self.assertFalse(vad.is_speech(bytes(640)))
        self.assertTrue(vad.is_speech(struct.pack("<320h", *([1200] * 320))))
        self.assertFalse(vad.is_speech(struct.pack("<320h", *([200] * 320))))

    def test_energy_vad_rejects_invalid_thresholds(self):
        for value in (-1, float("nan"), float("inf"), True, "500"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    EnergyVAD(threshold=value)

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
