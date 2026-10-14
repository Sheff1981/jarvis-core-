import unittest
from unittest.mock import Mock
from voice_chat import WakeAssistant


class ContinuousConversationTests(unittest.TestCase):
    def test_wake_once_then_continue(self):
        clock = [100]
        assistant = Mock()
        assistant.respond.side_effect = lambda phrase: "answer: " + phrase
        router = WakeAssistant(assistant, idle_seconds=300, clock=lambda: clock[0])
        self.assertIsNone(router.respond("как дела"))
        self.assertEqual("answer: привет", router.respond("Привет, Джарвис"))
        clock[0] += 30
        self.assertEqual("answer: как дела", router.respond("как дела"))
        clock[0] += 301
        self.assertIsNone(router.respond("как дела"))
        self.assertEqual(2, assistant.respond.call_count)

    def test_no_command_before_wake_even_when_it_sounds_like_an_action(self):
        assistant = Mock()
        router = WakeAssistant(assistant, clock=lambda: 100)
        self.assertIsNone(router.respond("открой блокнот"))
        assistant.respond.assert_not_called()

    def test_fresh_wake_reactivates(self):
        clock = [100]
        assistant = Mock()
        assistant.respond.return_value = "ok"
        router = WakeAssistant(assistant, idle_seconds=300, clock=lambda: clock[0])
        router.respond("джарвис привет")
        clock[0] += 301
        self.assertIsNone(router.respond("ещё вопрос"))
        self.assertEqual("ok", router.respond("джарвис продолжим"))


if __name__ == "__main__":
    unittest.main()
