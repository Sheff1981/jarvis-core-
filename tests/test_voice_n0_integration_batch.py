"""N0 integration: real coordinator with deterministic capture and assistant fakes."""
import threading
import unittest

from jarvis.voice_session import VoiceSession


class ScriptedInput:
    def __init__(self, phrases):
        self.phrases = phrases

    def listen(self, on_text, stop_event, should_listen=None):
        for phrase in self.phrases:
            if stop_event.is_set():
                return
            on_text(phrase)
            # Wait for the coordinator to consume the queued speech.
            stop_event.wait(0.03)
        stop_event.wait(0.15)


class DialogueStub:
    def close(self):
        pass


class AssistantStub:
    def __init__(self):
        self.action_dialogue = DialogueStub()
        self.calls = []

    def respond(self, text):
        self.calls.append(text)
        return "Ответ: " + text


class VoiceN0IntegrationBatch(unittest.TestCase):
    def test_wake_then_followup_without_second_wake(self):
        assistant = AssistantStub()
        session = VoiceSession(
            assistant, ScriptedInput(["привет джарвис", "как дела"]),
            require_wake=True)
        events = []
        session.run(lambda kind, value: events.append((kind, value)))
        self.assertIn("привет джарвис", assistant.calls)
        self.assertIn("как дела", assistant.calls)
        self.assertIn(("answer", "Ответ: как дела"), events)

    def test_sleep_disables_followup_until_wake(self):
        assistant = AssistantStub()
        session = VoiceSession(
            assistant, ScriptedInput(["джарвис", "спи", "как дела"]),
            require_wake=True)
        session.run(lambda kind, value: None)
        self.assertNotIn("как дела", assistant.calls)

    def test_unactivated_phrase_is_ignored(self):
        assistant = AssistantStub()
        session = VoiceSession(
            assistant, ScriptedInput(["как дела"]), require_wake=True)
        session.run(lambda kind, value: None)
        self.assertEqual(assistant.calls, [])


if __name__ == "__main__":
    unittest.main()
