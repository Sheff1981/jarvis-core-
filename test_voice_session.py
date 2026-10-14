import threading
import unittest
from jarvis.voice_session import VoiceSession


class FakeAssistant:
    def respond(self, phrase):
        return "Останавливаюсь." if phrase == "стоп" else "Понял."


class FakeMicrophone:
    def listen(self, on_text, stop_event, should_listen=None):
        on_text("стоп")
        stop_event.wait(1)


class BrokenMicrophone:
    def listen(self, on_text, stop_event, should_listen=None):
        raise RuntimeError("Устройство недоступно")


class EchoMicrophone:
    def __init__(self):
        self.emit = None
        self.ready = threading.Event()

    def listen(self, on_text, stop_event, should_listen=None):
        self.emit = on_text
        self.ready.set()
        on_text("привет")
        stop_event.wait(1)


class VoiceSessionTests(unittest.TestCase):
    def test_assistant_exception_stops_session_and_reports_error(self):
        class BrokenAssistant:
            def respond(self, phrase):
                raise ValueError("simulated failure")

        class Input:
            def listen(self, on_text, stop_event, should_listen=None):
                on_text("привет")
                stop_event.wait(1)

        events = []
        session = VoiceSession(BrokenAssistant(), Input())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertTrue(session.stop_event.is_set())
        self.assertTrue(any(kind == "error" and "simulated failure" in value
                            for kind, value in events))

    def test_empty_transcriptions_are_ignored(self):
        class Input:
            def listen(self, on_text, stop_event, should_listen=None):
                on_text("")
                on_text("   ")
                on_text("стоп")
                stop_event.wait(1)
        events = []
        session = VoiceSession(FakeAssistant(), Input())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual([("heard", "стоп")], [e for e in events if e[0] == "heard"])

    def test_routes_voice_and_stops(self):
        events = []
        session = VoiceSession(FakeAssistant(), FakeMicrophone())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertIn(("answer", "Останавливаюсь."), events)
        self.assertTrue(session.stop_event.is_set())

    def test_reports_microphone_error(self):
        events = []
        session = VoiceSession(FakeAssistant(), BrokenMicrophone())
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertIn(("error", "Устройство недоступно"), events)

    def test_does_not_process_echo_during_spoken_answer(self):
        microphone = EchoMicrophone()
        seen = []
        class Assistant:
            def respond(self, phrase):
                seen.append(phrase)
                return "Останавливаюсь."
        session = VoiceSession(Assistant(), microphone)
        def event(kind, value):
            if kind == "answer":
                self.assertTrue(microphone.ready.is_set())
                microphone.emit("это эхо динамиков")
        session.run(event)
        self.assertEqual(seen, ["привет"])
        self.assertTrue(session.stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
