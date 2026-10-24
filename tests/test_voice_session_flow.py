import unittest

from jarvis.voice_session import VoiceSession


class FakeAssistant:
    def __init__(self):
        self.received = []
        self.action_dialogue = self
        self.cancelled = False

    def respond(self, phrase):
        self.received.append(phrase)
        return "Понял."

    def close(self):
        self.cancelled = True


class FakeInput:
    def __init__(self, phrases):
        self.phrases = phrases

    def listen(self, callback, stop_event, should_listen):
        for phrase in self.phrases:
            callback(phrase)


class VoiceSessionFlowTests(unittest.TestCase):
    def test_wake_once_keeps_followup_and_sleep(self):
        assistant = FakeAssistant()
        events = []
        voice = VoiceSession(
            assistant,
            FakeInput(["посторонняя речь", "Джарвис, привет", "как дела", "спи"]),
            require_wake=True,
        )
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(assistant.received, ["привет", "как дела"])
        self.assertTrue(assistant.cancelled)
        self.assertFalse(voice.active)
        self.assertIn(("answer", "Перехожу в режим ожидания."), events)

    def test_existing_voice_flow_stays_active_without_wake(self):
        assistant = FakeAssistant()
        voice = VoiceSession(assistant, FakeInput(["проверка"]))
        voice.run(lambda *_: None)
        self.assertEqual(assistant.received, ["проверка"])
