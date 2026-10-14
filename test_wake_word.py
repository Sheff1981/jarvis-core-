import unittest
from jarvis.wake_word import extract_command


class WakeWordTests(unittest.TestCase):
    def test_greetings(self):
        for phrase in ("Привет, Джарвис", "Привет, Джервис!", "Jarvis"):
            with self.subTest(phrase=phrase):
                self.assertEqual(extract_command(phrase), (True, "привет"))

    def test_direct_commands(self):
        self.assertEqual(extract_command("Джарвис, какие проекты"), (True, "какие проекты"))
        self.assertEqual(extract_command("Джервис добавь проект LIZORIA"), (True, "добавь проект lizoria"))

    def test_ignores_other_conversations(self):
        self.assertEqual(extract_command("Привет, как дела?"), (False, ""))
        self.assertEqual(extract_command("Мы обсуждали Джарвиса"), (False, ""))


if __name__ == "__main__":
    unittest.main()
