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

    def test_named_greeting_punctuation_variants(self):
        for greeting in ("Привет, Джарвис", "Привет Джарвис",
                         "ПРИВЕТ, ДЖАРВИС!", "Привет,  Джарвис"):
            with self.subTest(greeting=greeting):
                assistant = FakeAssistant()
                voice = VoiceSession(assistant, FakeInput([greeting]),
                                     require_wake=True)
                voice.run(lambda *args: None)
                self.assertEqual(assistant.received, ["привет джарвис"])

    def test_sleep_requires_new_wake_phrase(self):
        assistant = FakeAssistant()
        events = []
        voice = VoiceSession(assistant, FakeInput([
            "джарвис проверка", "спи", "это нельзя выполнять",
            "джарвис продолжай",
        ]), require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(assistant.received, ["проверка", "продолжай"])
        self.assertIn(("answer", "Перехожу в режим ожидания."), events)
        assistant.action_dialogue.close.assert_called_once()

    def test_muted_microphone_discards_commands(self):
        assistant = FakeAssistant()
        controller = MagicMock()
        controller.muted = True
        controller.exit_requested = False
        voice = VoiceSession(assistant, FakeInput([
            "джарвис проверь",
        ]), controller=controller, require_wake=True)
        voice.run(lambda *args: None)
        self.assertEqual(assistant.received, [])

    def test_stop_response_ends_session(self):
        class StopAssistant(FakeAssistant):
            def respond(self, phrase):
                self.received.append(phrase)
                return "Останавливаюсь."

        assistant = StopAssistant()
        voice = VoiceSession(assistant, FakeInput([
            "джарвис заверши работу", "джарвис ещё команда",
        ]), require_wake=True)
        voice.run(lambda *args: None)
        self.assertEqual(assistant.received, ["заверши работу"])
        self.assertTrue(voice.stop_event.is_set())

    def test_assistant_failure_emits_error_and_stops(self):
        class BrokenAssistant(FakeAssistant):
            def respond(self, phrase):
                raise RuntimeError("synthetic failure")

        events = []
        voice = VoiceSession(BrokenAssistant(), FakeInput([
            "джарвис тест",
        ]), require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertTrue(voice.stop_event.is_set())
        self.assertTrue(any(kind == "error" and "synthetic failure" in value
                            for kind, value in events))
        self.assertFalse(voice.busy_event.is_set())

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
