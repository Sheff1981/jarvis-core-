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

    def test_new_session_after_stop_accepts_wake(self):
        class StopOnceAssistant(FakeAssistant):
            def respond(self, phrase):
                self.received.append(phrase)
                return "Останавливаюсь." if phrase == "заверши" else "Понял."

        assistant = StopOnceAssistant()
        first = VoiceSession(assistant, FakeInput(["джарвис заверши"]),
                             require_wake=True)
        first.run(lambda *args: None)
        self.assertTrue(first.stop_event.is_set())
        second = VoiceSession(assistant, FakeInput(["джарвис снова"]),
                              require_wake=True)
        second.run(lambda *args: None)
        self.assertEqual(assistant.received, ["заверши", "снова"])

    def test_conversation_history_restored_on_new_assistant(self):
        class HistoryLLM:
            def __init__(self):
                self.history = []
                self.max_turns = 2

            def ask(self, prompt):
                return "Ответ на: " + prompt

        with tempfile.TemporaryDirectory() as folder:
            db_path = str(Path(folder) / "history.db")
            first_llm = HistoryLLM()
            first = Assistant(db_path, llm=first_llm)
            try:
                first.conversations.append_exchange("первый вопрос", "первый ответ")
            finally:
                first.close()
            second_llm = HistoryLLM()
            second = Assistant(db_path, llm=second_llm)
            try:
                self.assertEqual(second_llm.history, [
                    {"role": "user", "content": "первый вопрос"},
                    {"role": "assistant", "content": "первый ответ"},
                ])
            finally:
                second.close()

    def test_microphone_capture_failure_emits_error_and_stops(self):
        class BrokenInput:
            def listen(self, callback, stop_event, should_listen):
                raise OSError("synthetic microphone unavailable")

        assistant = FakeAssistant()
        events = []
        voice = VoiceSession(assistant, BrokenInput(), require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertTrue(voice.stop_event.is_set())
        self.assertTrue(voice.capture_finished.is_set())
        self.assertIn(("error", "synthetic microphone unavailable"), events)
        self.assertEqual(assistant.received, [])

    def test_ten_sequential_dialogues_after_wake(self):
        assistant = FakeAssistant()
        phrases = ["джарвис проверка один"] + [
            "диалог " + str(number) for number in range(2, 11)
        ]
        events = []
        voice = VoiceSession(assistant, FakeInput(phrases), require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(len(assistant.received), 10)
        self.assertEqual(assistant.received[0], "проверка один")
        self.assertEqual(assistant.received[-1], "диалог 10")
        self.assertEqual(sum(kind == "answer" for kind, _ in events), 10)
        self.assertFalse(any(kind == "error" for kind, _ in events))

    def test_capture_error_survives_speech_queue_cleanup(self):
        class InputWithFailure:
            def listen(self, callback, stop_event, should_listen):
                callback("джарвис проверка")
                raise OSError("synthetic capture failure after speech")

        assistant = FakeAssistant()
        events = []
        voice = VoiceSession(assistant, InputWithFailure(), require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(assistant.received, ["проверка"])
        self.assertIn(("error", "synthetic capture failure after speech"), events)
        self.assertTrue(voice.stop_event.is_set())

    def test_speech_queued_during_answer_is_not_executed(self):
        class InputDuringReply:
            def __init__(self):
                self.callback = None

            def listen(self, callback, stop_event, should_listen):
                self.callback = callback
                callback("джарвис первая команда")

        class AssistantDuringReply(FakeAssistant):
            def respond(self, phrase):
                self.received.append(phrase)
                if phrase == "первая команда":
                    input_device.callback("опасная команда во время ответа")
                return "Понял."

        input_device = InputDuringReply()
        assistant = AssistantDuringReply()
        events = []
        voice = VoiceSession(assistant, input_device, require_wake=True)
        voice.run(lambda kind, value: events.append((kind, value)))
        self.assertEqual(assistant.received, ["первая команда"])
        self.assertFalse(any(kind == "error" for kind, _ in events))

    def test_next_utterance_after_answer_is_accepted(self):
        class TwoTurnInput:
            def __init__(self):
                self.callback = None

            def listen(self, callback, stop_event, should_listen):
                self.callback = callback
                callback("джарвис первая команда")

        class TwoTurnAssistant(FakeAssistant):
            def respond(self, phrase):
                self.received.append(phrase)
                return "Понял."

        input_device = TwoTurnInput()
        assistant = TwoTurnAssistant()
        events = []
        voice = VoiceSession(assistant, input_device, require_wake=True)

        def on_event(kind, value):
            events.append((kind, value))
            if kind == "answer" and value == "Понял." and len(assistant.received) == 1:
                # Speech delivered while feedback is active must be rejected.
                input_device.callback("фраза во время озвучивания")

        voice.run(on_event)
        self.assertEqual(assistant.received, ["первая команда"])
        self.assertFalse(voice.busy_event.is_set())

    def test_followup_after_first_answer_without_second_wake(self):
        class FollowupInput:
            def __init__(self):
                self.callback = None
                self.ready_for_followup = False

            def listen(self, callback, stop_event, should_listen):
                self.callback = callback
                callback("джарвис первая команда")
                # Wait until the first response has finished processing.
                while not stop_event.is_set() and not self.ready_for_followup:
                    stop_event.wait(0.001)
                while not stop_event.is_set() and not should_listen():
                    stop_event.wait(0.001)
                if not stop_event.is_set():
                    callback("вторая команда")

        class FollowupAssistant(FakeAssistant):
            def respond(self, phrase):
                self.received.append(phrase)
                return "Ответ " + str(len(self.received))

        input_device = FollowupInput()
        assistant = FollowupAssistant()
        events = []
        voice = VoiceSession(assistant, input_device, require_wake=True)

        def on_event(kind, value):
            events.append((kind, value))
            if kind == "answer" and value == "Ответ 1":
                input_device.ready_for_followup = True

        voice.run(on_event)
        self.assertEqual(assistant.received, ["первая команда", "вторая команда"])
        self.assertEqual([v for k, v in events if k == "answer"],
                         ["Ответ 1", "Ответ 2"])

    def test_control_replies_block_microphone_feedback(self):
        class FeedbackInput:
            def __init__(self):
                self.callback = None

            def listen(self, callback, stop_event, should_listen):
                self.callback = callback
                callback("джарвис")
                callback("спи")

        assistant = FakeAssistant()
        input_device = FeedbackInput()
        voice = VoiceSession(assistant, input_device, require_wake=True)
        gate_during_answers = []

        def on_event(kind, value):
            if kind == "answer":
                gate_during_answers.append((value, voice.busy_event.is_set()))
                input_device.callback("джарвис команда из динамиков")

        voice.run(on_event)
        self.assertEqual(gate_during_answers, [
            ("Слушаю.", True),
            ("Перехожу в режим ожидания.", True),
        ])
        self.assertEqual(assistant.received, [])
        self.assertFalse(voice.busy_event.is_set())

    def test_error_callback_failure_still_stops_microphone(self):
        class BrokenAssistant(FakeAssistant):
            def respond(self, phrase):
                raise RuntimeError("synthetic assistant failure")

        voice = VoiceSession(BrokenAssistant(),
                             FakeInput(["джарвис проверка"]), require_wake=True)

        def broken_callback(kind, value):
            if kind == "error":
                raise OSError("synthetic error reporter failure")

        with self.assertRaisesRegex(OSError, "error reporter failure"):
            voice.run(broken_callback)
        self.assertTrue(voice.stop_event.is_set())
        self.assertTrue(voice.capture_finished.is_set())
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
