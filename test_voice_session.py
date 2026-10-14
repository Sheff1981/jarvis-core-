import unittest
from jarvis.voice_session import VoiceSession


class FakeAssistant:
    def respond(self, phrase):
        return "Останавливаюсь." if phrase == "стоп" else "Понял."


class FakeMicrophone:
    def listen(self, on_text, stop_event):
        on_text("привет")
        on_text("стоп")


class BrokenMicrophone:
    def listen(self, on_text, stop_event):
        raise RuntimeError("Устройство недоступно")


class VoiceSessionTests(unittest.TestCase):
    def test_routes_voice_and_stops(self):
        events = []
        session = VoiceSession(FakeAssistant(), FakeMicrophone())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertIn(("answer", "Понял."), events)
        self.assertIn(("answer", "Останавливаюсь."), events)
        self.assertTrue(session.stop_event.is_set())

    def test_reports_microphone_error(self):
        events = []
        session = VoiceSession(FakeAssistant(), BrokenMicrophone())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertIn(("error", "Устройство недоступно"), events)
        self.assertTrue(session.stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
