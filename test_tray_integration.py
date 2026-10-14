import unittest
from jarvis.tray import TrayController
from jarvis.voice_session import VoiceSession


class DummyAssistant:
    def respond(self, text):
        return "Понял."


class DummyInput:
    def listen(self, callback, stop_event, should_listen=None):
        stop_event.wait(0.05)


class TrayIntegrationTests(unittest.TestCase):
    def test_mute_blocks_recognition(self):
        controller = TrayController()
        session = VoiceSession(DummyAssistant(), DummyInput(), controller)
        self.assertTrue(session.listening_allowed())
        controller.toggle_mute()
        self.assertFalse(session.listening_allowed())
        controller.toggle_mute()
        self.assertTrue(session.listening_allowed())
        session.busy_event.set()
        self.assertFalse(session.listening_allowed())
        session.busy_event.clear()
        session.request_stop()
        self.assertFalse(session.listening_allowed())

    def test_exit_request_is_observable(self):
        controller = TrayController()
        session = VoiceSession(DummyAssistant(), DummyInput(), controller)
        controller.request_exit()
        events = []
        session.run(lambda kind, value: events.append(kind))
        self.assertTrue(session.stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
