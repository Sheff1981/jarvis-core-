import unittest
from jarvis.wake import WakeDispatcher, GREETINGS, is_wake_phrase


class WakeTests(unittest.TestCase):
    def test_name_detection(self):
        for phrase in ("Джарвис, привет", "джервис откройся", "Жарвис"):
            self.assertTrue(is_wake_phrase(phrase))
        for phrase in ("привет", "расскажи про Джарвиса", "Джарвисов проект", ""):
            self.assertFalse(is_wake_phrase(phrase))

    def test_greeting_and_cooldown(self):
        opened, spoken = [], []
        now = [100.0]
        wake = WakeDispatcher(open_fn=opened.append, say_fn=spoken.append,
                              choice_fn=lambda choices: choices[0],
                              clock=lambda: now[0], cooldown=8)
        self.assertTrue(wake.handle("Джарвис привет"))
        self.assertFalse(wake.handle("Джарвис привет"))
        self.assertEqual(opened, ["http://127.0.0.1:8765"])
        self.assertEqual(spoken, [GREETINGS[0]])
        now[0] += 9
        self.assertTrue(wake.handle("Джарвис"))
        self.assertEqual(len(opened), 2)

    def test_silent_mode(self):
        opened = []
        wake = WakeDispatcher(open_fn=opened.append)
        self.assertTrue(wake.handle("джарвис"))
        self.assertEqual(len(opened), 1)


if __name__ == "__main__":
    unittest.main()
