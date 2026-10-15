"""Verify voice response latency instrumentation."""
import unittest
from unittest.mock import Mock

from jarvis.voice_session import VoiceSession


class VoiceLatencyTests(unittest.TestCase):
    def test_latency_starts_unset(self):
        session = VoiceSession(Mock(), Mock(), require_wake=False)
        self.assertIsNone(session.last_timings)

    def test_voice_session_uses_monotonic_clock_for_wake(self):
        session = VoiceSession(Mock(), Mock(), require_wake=True, clock=lambda: 10)
        self.assertFalse(session.active)
        self.assertEqual(session.active_until, 0)


if __name__ == "__main__":
    unittest.main()
