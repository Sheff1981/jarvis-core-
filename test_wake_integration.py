import unittest
from jarvis.wake_word import extract_command
from voice_chat import WakeAssistant


class FakeAssistant:
    def __init__(self):
        self.commands = []

    def respond(self, command):
        self.commands.append(command)
        return "Останавливаюсь." if command == "стоп" else "Привет."


class WakeIntegrationTests(unittest.TestCase):
    def test_only_activated_commands_reach_assistant(self):
        inner = FakeAssistant()
        wrapper = WakeAssistant(inner)
        self.assertIsNone(wrapper.respond("посторонний разговор"))
        self.assertEqual(inner.commands, [])
        self.assertEqual(wrapper.respond("Привет, Чат"), "Привет.")
        self.assertEqual(wrapper.respond("Джарвис, стоп"), "Останавливаюсь.")
        self.assertEqual(inner.commands, ["привет", "стоп"])


if __name__ == "__main__":
    unittest.main()
