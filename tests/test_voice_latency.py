"""Verify voice response latency instrumentation."""
import unittest
from unittest.mock import Mock
import threading

from jarvis.voice_session import VoiceSession


class VoiceLatencyTests(unittest.TestCase):
    def test_latency_starts_unset(self):
        session = VoiceSession(Mock(), Mock(), require_wake=False)
        self.assertIsNone(session.last_timings)

    def test_local_command_does_not_reuse_old_llm_metrics(self):
        llm = Mock()
        llm.last_metrics = {"load_ms": 900}
        assistant = Mock()
        assistant.llm = llm
        assistant.respond.return_value = "Незавершённых проектов нет."

        class Input:
            def listen(self, callback, stop_event, should_listen=None):
                callback("какие у нас проекты")
                stop_event.wait(0.3)

        session = VoiceSession(assistant, Input(), require_wake=False)
        received = []

        def on_event(kind, value):
            received.append((kind, value))
            if kind == "answer":
                session.request_stop()

        session.run(on_event)
        self.assertEqual(llm.last_metrics, None)
        self.assertFalse(session.last_timings["llm_used"])
        self.assertGreaterEqual(session.last_timings["assistant_ms"], 0)
        self.assertTrue(any(kind == "answer" for kind, _ in received))

    def test_voice_session_uses_monotonic_clock_for_wake(self):
        session = VoiceSession(Mock(), Mock(), require_wake=True, clock=lambda: 10)
        self.assertFalse(session.active)
        self.assertEqual(session.active_until, 0)


if __name__ == "__main__":
    unittest.main()
