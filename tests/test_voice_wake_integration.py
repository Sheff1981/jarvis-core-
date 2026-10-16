"""Integration checks: voice uses one wake gate and expires after inactivity."""
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import voice_chat
from jarvis.voice_session import VoiceSession
from jarvis.assistant import Assistant


class FakeInput:
    def __init__(self, phrases):
        self.phrases = phrases

    def listen(self, callback, stop_event, should_listen):
        for phrase in self.phrases:
            callback(phrase)


class FakeAssistant:
    def __init__(self):
        self.received = []
        self.action_dialogue = MagicMock()

    def respond(self, phrase):
        self.received.append(phrase)
        return "Понял."


class VoiceWakeIntegrationTests(unittest.TestCase):
    def test_entrypoint_passes_actual_assistant_not_second_wake_router(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--model", "vosk-model"]), \
             patch("voice_chat.Assistant") as assistant, \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession") as session, \
             patch("voice_chat.Speaker"):
            voice_chat.main()
        self.assertIs(session.call_args.args[0], assistant.return_value)
        self.assertTrue(session.call_args.kwargs["require_wake"])

    def test_always_listen_disables_wake_requirement(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--model", "vosk-model", "--always-listen"]), \
             patch("voice_chat.Assistant"), \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession") as session, \
             patch("voice_chat.Speaker"):
            voice_chat.main()
        self.assertFalse(session.call_args.kwargs["require_wake"])

    def test_existing_russian_wake_parser_supports_dzhervis(self):
        assistant = FakeAssistant()
        voice = VoiceSession(assistant, FakeInput([
            "посторонняя фраза", "джервис привет", "как дела", "спи",
            "говори", "джарвис проверка",
        ]), require_wake=True)
        voice.run(lambda *args: None)
        self.assertEqual(assistant.received, ["привет", "как дела", "проверка"])
        assistant.action_dialogue.close.assert_called_once()

    def test_named_greeting_reaches_assistant_unchanged(self):
        assistant = FakeAssistant()
        voice = VoiceSession(assistant, FakeInput([
            "Привет, Джарвис",
        ]), require_wake=True)
        voice.run(lambda *args: None)
        self.assertEqual(assistant.received, ["привет джарвис"])

    def test_named_greeting_uses_real_assistant_local_reply(self):
        class StubLLM:
            def __init__(self):
                self.prompts = []

            def ask(self, prompt):
                self.prompts.append(prompt)
                return "Не должно вызываться"

        with tempfile.TemporaryDirectory() as folder:
            llm = StubLLM()
            assistant = Assistant(str(Path(folder) / "voice.db"), llm=llm)
            events = []
            try:
                voice = VoiceSession(assistant, FakeInput(["Привет, Джарвис"]),
                                     require_wake=True)
                voice.run(lambda kind, value: events.append((kind, value)))
                self.assertIn(("answer", "Привет, Саня. Я заговорил!"), events)
                self.assertEqual(llm.prompts, [])
            finally:
                assistant.close()

    def test_wake_expires_after_idle_timeout(self):
        assistant = FakeAssistant()
        ticks = iter([0, 10, 311, 312])
        voice = VoiceSession(assistant, FakeInput([
            "джарвис привет", "как дела", "это должно быть проигнорировано",
            "джарвис снова привет",
        ]), require_wake=True, clock=lambda: next(ticks))
        voice.run(lambda *args: None)
        self.assertEqual(assistant.received, ["привет", "как дела", "снова привет"])


if __name__ == "__main__":
    unittest.main()
