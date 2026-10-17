"""Wake, dialogue, sleep and reactivation integration tests."""
import unittest
from unittest.mock import Mock

from jarvis.voice_session import VoiceSession


class ScriptedInput:
    def __init__(self, phrases):
        self.phrases = phrases

    def listen(self, callback, stop_event, should_listen=None):
        for phrase in self.phrases:
            if stop_event.is_set():
                break
            callback(phrase)
            # Wait for the consumer to handle each phrase before injecting the next.
            import time
            time.sleep(0.03)
        stop_event.wait(0.3)


class VoiceWakeLifecycleTests(unittest.TestCase):
    def test_sleep_blocks_commands_until_new_wake(self):
        assistant = Mock()
        assistant.respond.return_value = "Ответ."
        session = VoiceSession(assistant, ScriptedInput([
            "джарвис привет",
            "спи",
            "какие у нас проекты",
            "джарвис какие у нас проекты",
        ]), require_wake=True)
        answers = []

        def on_event(kind, value):
            if kind == "answer":
                answers.append(value)
                if len(answers) == 3:
                    session.request_stop()

        session.run(on_event)
        self.assertEqual(assistant.respond.call_count, 2)
        self.assertEqual(assistant.respond.call_args_list[0].args[0], "привет")
        self.assertEqual(assistant.respond.call_args_list[1].args[0], "какие у нас проекты")
        self.assertIn("Перехожу в режим ожидания.", answers)

    def test_unactivated_speech_is_ignored(self):
        assistant = Mock()
        session = VoiceSession(assistant, ScriptedInput(["какие у нас проекты"]), require_wake=True)
        session.run(lambda kind, value: None)
        assistant.respond.assert_not_called()


if __name__ == "__main__":
    unittest.main()
