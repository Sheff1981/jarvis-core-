import unittest
from jarvis.voice_session import VoiceSession


class VoiceWakeTests(unittest.TestCase):
    def test_wake_is_opt_in_for_existing_clients(self):
        assistant = object()
        microphone = object()
        self.assertTrue(VoiceSession(assistant, microphone).active)
        self.assertFalse(VoiceSession(assistant, microphone, require_wake=True).active)
