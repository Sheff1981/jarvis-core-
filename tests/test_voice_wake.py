import threading
import unittest
from jarvis.voice_session import VoiceSession


class FakeMicrophone:
    def __init__(self, phrases):
        self.phrases = phrases

    def listen(self, recognized, stop_event, should_listen):
        for phrase in self.phrases:
            recognized(phrase)


class FakeAssistant:
    def __init__(self):
        self.phrases = []
        self.action_dialogue = self
        self.cancelled = False

    def close(self):
        self.cancelled = True

    def respond(self, phrase):
        self.phrases.append(phrase)
        return "Ответ"


class VoiceWakeTests(unittest.TestCase):
    def test_wake_once_and_sleep(self):
        assistant = FakeAssistant()
        voice = VoiceSession(assistant, FakeMicrophone([]), require_wake=True)
        events = []
        voice.input_device = FakeMicrophone(["Привет", "Джарвис, привет", "как дела", "спи"])
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(assistant.phrases[:1], ["привет"])
